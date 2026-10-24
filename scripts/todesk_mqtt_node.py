#!/usr/bin/python3
# todesk_mqtt_node.py

import json
import os
import subprocess
import sys

import rospy
import paho.mqtt.client as mqtt

# tomllib 兼容：python>=3.11内置，低版本用tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def _log(level, msg):
    log_map = {
        "debug": rospy.logdebug,
        "info": rospy.loginfo,
        "warn": rospy.logwarn,
        "error": rospy.logerr,
        "fatal": rospy.logfatal,
    }
    if level in log_map:
        log_map[level](msg)


def load_toml(cfg_path):
    if not os.path.exists(cfg_path):
        _log("error", f"config.toml not found: {cfg_path}")
        return None
    try:
        with open(cfg_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        _log("error", f"parse toml failed: {e}")
        return None


client = None


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        _log("info", f"MQTT connected, subscribe {userdata['sub_topic']}")
        client.subscribe(userdata["sub_topic"], qos=1)
    else:
        _log("error", f"mqtt connect fail reason={reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    if reason_code != 0:
        _log("warn", f"MQTT disconnected, reason={reason_code}")


def on_message(client, userdata, msg):
    seq = 0
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        action = data.get("action")
        seq = data.get("seq", 0)
        if action == "restart_todesk":
            _log("info", f"Receive restart todeskd command seq={seq}")
            try:
                ret = subprocess.run(
                    ["sudo", "/usr/bin/systemctl", "restart", "todeskd.service"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=15,
                )
                if ret.returncode == 0:
                    res = {"result": "ok", "msg": "restart triggered", "seq": seq}
                    _log("info", "todeskd restart ok")
                else:
                    stderr_msg = (
                        ret.stderr.decode("utf-8", "ignore").strip()
                        if ret.stderr
                        else ""
                    )
                    res = {
                        "result": "fail",
                        "msg": f"systemctl return non-zero rc={ret.returncode}: {stderr_msg}",
                        "seq": seq,
                    }
                    _log(
                        "error",
                        f"restart fail: rc={ret.returncode}, stderr={stderr_msg}",
                    )
            except subprocess.TimeoutExpired:
                res = {"result": "fail", "msg": "systemctl restart timeout", "seq": seq}
                _log("error", "restart fail: systemctl restart timeout")
            except Exception as e:
                res = {"result": "fail", "msg": f"exec error: {e}", "seq": seq}
                _log("error", f"restart fail: exec error: {e}")

            client.publish(userdata["pub_topic"], json.dumps(res), qos=1)
        else:
            _log("warn", f"unknown action={action!r}, seq={seq}")
    except Exception as e:
        _log("error", f"parse mqtt msg err: {e}")
        try:
            res = {"result": "fail", "msg": f"parse error: {e}", "seq": seq}
            client.publish(userdata["pub_topic"], json.dumps(res), qos=1)
        except Exception as e2:
            _log("error", f"publish fail res err: {e2}")


def main():
    global client

    rospy.init_node("todesk_mqtt")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_file = os.path.join(script_dir, "config.toml")
    cfg = load_toml(cfg_file)
    if cfg is None:
        rospy.signal_shutdown("load config.toml error")
        return

    mqtt_cfg = cfg.get("mqtt")
    if not isinstance(mqtt_cfg, dict):
        _log("error", "config.toml missing [mqtt] section")
        rospy.signal_shutdown("invalid config.toml")
        return

    dev_id = str(mqtt_cfg.get("dev_id", "")).strip()
    broker = str(mqtt_cfg.get("broker", "")).strip()
    port_raw = mqtt_cfg.get("port", 1883)
    if not dev_id or "/" in dev_id:
        _log("error", f"invalid dev_id: {dev_id!r}")
        rospy.signal_shutdown("invalid dev_id")
        return
    if not broker:
        _log("error", "config.toml missing mqtt.broker")
        rospy.signal_shutdown("invalid broker")
        return
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        _log("error", f"invalid mqtt.port: {port_raw!r}")
        rospy.signal_shutdown("invalid port")
        return

    m_user = mqtt_cfg.get("user", "")
    m_pass = mqtt_cfg.get("pass", "")
    ka = int(mqtt_cfg.get("keepalive", 60))

    sub_topic = f"cmd/device/{dev_id}/todesk"
    pub_topic = f"state/device/{dev_id}/todesk"
    userdata = {"sub_topic": sub_topic, "pub_topic": pub_topic}

    client = mqtt.Client(
        client_id=f"ros_todesk_{dev_id}",
        userdata=userdata,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    if m_user:
        client.username_pw_set(m_user, m_pass)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(broker, port, keepalive=ka)
    except Exception as e:
        _log("error", f"connect broker error: {e}")
        rospy.signal_shutdown("mqtt connect error")
        return

    client.loop_start()
    _log("info", "todesk mqtt ros node started")
    try:
        rospy.spin()
    finally:
        _log("info", "node shutdown, stop mqtt loop")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
