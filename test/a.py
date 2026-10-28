import json

import paho.mqtt.client as mqtt

BROKER = "106.15.2.226"
PORT = 1883

DEV_ID = "a"
TOPIC = f"status/device/{DEV_ID}/todesk"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print("连接失败: %s", reason_code)


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=DEV_ID
)

client.on_connect = on_connect

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    # # payload 中也可以传 dev_id
    ack = json.dumps(
        {"dev_id": DEV_ID, "action": "restart_todesk", "status": "triggered"}
    )
    client.publish(TOPIC, ack, qos=1)
finally:
    client.disconnect()
    client.loop_stop()
