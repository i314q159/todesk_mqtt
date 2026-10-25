import json
import threading
import subprocess
import time

import utils_logger


import paho.mqtt.client as mqtt

# 冷却锁 5 秒
last_run_ts = 0
COOLDOWN = 5


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"connect failed: {reason_code}")
        return
    print(f"connected, sub: {userdata['sub_topic']}")
    client.subscribe(userdata["sub_topic"], qos=1)


# TODO - 执行命令操作，函数封装
# TODO - 服务端拿到返回的 seq，幂等
def on_message(client, userdata, msg):
    # seq = 0
    global last_run_ts
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        action = data.get("action")
        # seq = data.get("seq", 0)

        if action == "restart_todesk":
            now = time.time()
            if now - last_run_ts < COOLDOWN:
                utils_logger.log.warning("todeskd.service restart cooldown")
                utils_logger.log_flush()
                return

            threading.Thread(target=restart_todesk, daemon=True).start()

            last_run_ts = now

            utils_logger.log.info("todeskd.service restart trigger")
            utils_logger.log_flush()

    except Exception as e:
        utils_logger.log.error(f"on_message err: {e}")
        utils_logger.log_flush()


def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code.value != 0:
        print(f"disconnect unexpected, rc={reason_code.value}")


def restart_todesk():
    subprocess.run(
        ["sudo", "/usr/bin/systemctl", "restart", "todeskd.service"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# TLS 支持
def init_client(dev_id, user, password):
    sub_topic = f"cmd/device/{dev_id}/todesk"
    pub_topic = f"state/device/{dev_id}/todesk"
    userdata = {"sub_topic": sub_topic, "pub_topic": pub_topic}

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"ros_todesk_{dev_id}",
        userdata=userdata,
    )

    client.username_pw_set(user, password)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    return client
