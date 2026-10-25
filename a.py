import json
import time
import threading
import subprocess

COOLDOWN = 10
last_run_ts = 0
handled_seq = set()
MAX_SEQ_CACHE = 200


def restart_todesk():
    try:
        subprocess.run(["systemctl", "restart", "todeskd.service"], check=True)
    except subprocess.CalledProcessError as e:
        utils_logger.log.error(f"restart todeskd failed: {e}")
        utils_logger.log_flush()


def on_message(client, userdata, msg):
    global last_run_ts
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        action = data.get("action")
        seq = data.get("seq")
        # dev_id = userdata.get("dev_id") # 当前userdata没有传入，暂不用

        if seq is not None:
            if seq in handled_seq:
                utils_logger.log.warning(f"duplicate seq skip: {seq}")
                utils_logger.log_flush()
                return
            handled_seq.add(seq)
            if len(handled_seq) > MAX_SEQ_CACHE:
                handled_seq.pop()

        if action == "restart_todesk":
            now = time.time()
            if now - last_run_ts < COOLDOWN:
                utils_logger.log.warning(f"todeskd.service restart cooldown, seq={seq}")
                utils_logger.log_flush()
                # 冷却拦截应答
                ack = json.dumps(
                    {
                        "seq": seq,
                        "action": "restart_todesk",
                        "status": "rejected",
                        "reason": "cooldown",
                    }
                )
                client.publish(userdata["pub_topic"], ack, qos=1)
                return

            threading.Thread(target=restart_todesk, daemon=True).start()
            last_run_ts = now
            utils_logger.log.info(f"todeskd.service restart trigger, seq={seq}")
            utils_logger.log_flush()
            # 触发成功应答
            ack = json.dumps(
                {"seq": seq, "action": "restart_todesk", "status": "triggered"}
            )
            client.publish(userdata["pub_topic"], ack, qos=1)

    except Exception as e:
        utils_logger.log.error(f"on_message err: {e}")
        utils_logger.log_flush()
