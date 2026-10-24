#!/usr/bin/python3

# todesk_mqtt_node.py

import json
import logging
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


class _DevFilter(logging.Filter):
    def __init__(self, dev_id):
        super().__init__()
        self.dev_id = dev_id

    def filter(self, record):
        record.dev_id = self.dev_id
        return True


def _setup_file_log(dev_id=""):
    # 日志统一写到 ../log/（相对 scripts 目录，即 src/todesk_mqtt/log/）
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "log")
    os.makedirs(log_dir, exist_ok=True)
    import logging.handlers

    fh = logging.handlers.TimedRotatingFileHandler(
        os.path.join(log_dir, "todesk_mqtt.log"),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    fh.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] [dev=%(dev_id)s] %(message)s")
    )
    log = logging.getLogger("todesk_mqtt")
    log.setLevel(logging.INFO)
    log.addFilter(_DevFilter(dev_id))
    log.addHandler(fh)
    return log


LOG = None
DEV_ID = ""


# 双写：屏幕（rospy）+ 文件（log/todesk_mqtt.log）
def _log(level, msg):
    log_map = {
        "debug": ("debug", "logdebug"),
        "info": ("info", "loginfo"),
        "warn": ("warning", "logwarn"),
        "error": ("error", "logerr"),
        "fatal": ("critical", "logfatal"),
    }
    if level not in log_map:
        return

    log_lv, rospy_lv = log_map[level]
    if LOG is not None:
        getattr(LOG, log_lv)(msg)

    tag = f"[dev={DEV_ID}] " if DEV_ID else ""
    getattr(rospy, rospy_lv)(f"{tag}{msg}")


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


def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        _log("info", f"MQTT connected, subscribe {userdata['sub_topic']}")
        client.subscribe(userdata["sub_topic"], qos=1)
    else:
        _log("error", f"mqtt connect fail rc={rc}")


def on_disconnect(client, userdata, rc, properties):
    if rc != 0:
        _log("warn", f"MQTT disconnected, rc={rc}")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        action = data.get("action")
        seq = data.get("seq", 0)
        if action == "restart_todesk":
            _log("warn", f"Receive restart todeskd command seq={seq}")
            ret = subprocess.run(
                ["sudo", "/usr/bin/systemctl", "restart", "todeskd.service"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if ret.returncode == 0:
                res = {"result": "ok", "msg": "restart triggered", "seq": seq}
                _log("info", "todeskd restart ok")
            else:
                res = {"result": "fail", "msg": "systemctl return non-zero", "seq": seq}
                _log("error", "restart fail: systemctl return non-zero")

            client.publish(userdata["pub_topic"], json.dumps(res), qos=1)
    except Exception as e:
        _log("error", f"parse mqtt msg err: {e}")


def main():
    global LOG, DEV_ID
    rospy.init_node("todesk_mqtt")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_file = os.path.join(script_dir, "config.toml")
    cfg = load_toml(cfg_file)
    if cfg is None:
        rospy.signal_shutdown("load config.toml error")
        return

    mqtt_cfg = cfg["mqtt"]
    dev_id = mqtt_cfg["dev_id"]
    DEV_ID = dev_id
    LOG = _setup_file_log(dev_id)
    broker = mqtt_cfg["broker"]
    port = int(mqtt_cfg["port"])
    m_user = mqtt_cfg.get("user", "")
    m_pass = mqtt_cfg.get("pass", "")
    ka = int(mqtt_cfg.get("keepalive", 60))

    sub_topic = f"cmd/device/{dev_id}/todesk"
    pub_topic = f"state/device/{dev_id}/todesk"

    userdata = {"sub_topic": sub_topic, "pub_topic": pub_topic}

    global client
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
    rospy.spin()
    client.loop_stop()


if __name__ == "__main__":
    main()
