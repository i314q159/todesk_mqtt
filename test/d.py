import logging

import paho.mqtt.client as mqtt

BROKER = "106.15.2.226"
PORT = 1883

# 通配订阅
TOPIC = "status/device/+/todesk"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("mqtt-sub")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        log.error("连接失败: %s", reason_code)
        return
    log.info("已连接 broker (reason_code=%s)", reason_code)
    client.subscribe(TOPIC, qos=1)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8", errors="replace")
    except Exception:
        payload = repr(msg.payload)

    # msg.topic status/device/+/todesk

    # {msg.topic.split("/")[2]
    # status    device  +   todesk
    # 0         1       2   3

    # payload 中也可以传 dev_id
    log.info(
        f"d receiver | topic: {msg.topic} | dev_id: {msg.topic.split("/")[2]} | payload: {payload}",
    )


def on_disconnect(client, userdata, flags, reason_code, properties):
    log.warning("已断开: %s", reason_code)


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    clean_session=True,
)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect


client.connect(BROKER, PORT, keepalive=60)
try:
    client.loop_forever()
except KeyboardInterrupt:
    log.info("收到 Ctrl+C，退出")
finally:
    client.disconnect()
    client.loop_stop()
