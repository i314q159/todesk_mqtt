import json
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"connect failed: {reason_code}")
        return
    print(f"connected, sub: {userdata['sub_topic']}")
    client.subscribe(userdata["sub_topic"], qos=1)


# TODO - 执行命令操作，函数封装
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8", errors="ignore")
        print(f"recv [{msg.topic}]: {payload}")
    except Exception as e:
        print(f"on_message decode err: {e}")


def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code.value != 0:
        print(f"disconnect unexpected, rc={reason_code.value}")


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
