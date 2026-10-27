import json
import threading
import subprocess
import time

import utils_logger

from collections import OrderedDict
from threading import Lock

import paho.mqtt.client as mqtt

# 冷却时间，单位秒
COOLDOWN = 5
last_run_ts = 0

# 幂等缓存：记录已经处理过的 seq
handled_seq = OrderedDict()
MAX_SEQ_CACHE = 200
seq_lock = Lock()


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        utils_logger.log.error(f"connect failed: {reason_code}")
        utils_logger.log_flush()
        return

    utils_logger.log.info(f"MQTT connected, sub: {userdata['sub_topic']}")
    utils_logger.log_flush()

    client.subscribe(userdata["sub_topic"], qos=1)


def on_message(client, userdata, msg):
    global last_run_ts
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        action = data.get("action")
        seq = data.get("seq")

        if seq is not None:
            with seq_lock:
                if seq in handled_seq:
                    utils_logger.log.warning(f"duplicate seq skip: {seq}")
                    utils_logger.log_flush()

                    ack = json.dumps(
                        {
                            "seq": seq,
                            "action": action,
                            "status": "rejected",
                            "reason": "duplicate",
                        }
                    )
                    client.publish(userdata["pub_topic"], ack, qos=1)
                    return

                handled_seq[seq] = None
                if len(handled_seq) > MAX_SEQ_CACHE:
                    handled_seq.popitem(last=False)

        if action == "restart_todesk":
            now = time.time()
            if now - last_run_ts < COOLDOWN:
                utils_logger.log.warning(f"todeskd.service restart cooldown, seq={seq}")
                utils_logger.log_flush()
                # 冷却拦截应答
                ack = json.dumps(
                    {
                        "seq": seq,
                        "action": action,
                        "status": "rejected",
                        "reason": "cooldown",
                    }
                )
                client.publish(userdata["pub_topic"], ack, qos=1)
                return

            last_run_ts = now

            threading.Thread(target=restart_todesk, daemon=True).start()
            utils_logger.log.info(f"todeskd.service restart trigger, seq={seq}")
            utils_logger.log_flush()

            ack = json.dumps({"seq": seq, "action": action, "status": "triggered"})
            client.publish(userdata["pub_topic"], ack, qos=1)

    except Exception as e:
        utils_logger.log.error(f"on_message err: {e}")
        utils_logger.log_flush()


def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        utils_logger.log.error(f"disconnect unexpected, rc={reason_code.value}")
        utils_logger.log_flush()
    else:
        utils_logger.log.info(f"mqtt disconnected normally")
        utils_logger.log_flush()


def restart_todesk():
    try:
        subprocess.run(
            ["sudo", "/usr/bin/systemctl", "restart", "todeskd.service"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        utils_logger.log.error(f"restart todeskd.service failed: {e}")
        utils_logger.log_flush()


# TLS 支持（预留，需要的时候再加）
def init_client(dev_id, user, password):
    sub_topic = f"cmd/device/{dev_id}/todesk"
    pub_topic = f"state/device/{dev_id}/todesk"
    userdata = {
        "sub_topic": sub_topic,
        "pub_topic": pub_topic,
    }
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"{dev_id}",
        userdata=userdata,
    )
    client.username_pw_set(user, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    return client
