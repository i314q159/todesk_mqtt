#!/usr/bin/python3

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# import scripts.utils_toml as utils_toml
# import scripts.utils_mqtt as utils_mqtt

import utils_toml
import utils_mqtt

import rospy
import rospkg


def main():
    rospy.init_node("todesk_mqtt_node")

    # script_dir = os.path.dirname(os.path.abspath(__file__))
    pkg_path = rospkg.RosPack().get_path("todesk_mqtt")
    cfg_file = os.path.join(pkg_path, "config.toml")

    cfg = utils_toml.load_toml(cfg_file)
    mqtt = cfg.mqtt

    client = utils_mqtt.init_client(
        dev_id=mqtt.dev_id, user=mqtt.user, password=mqtt.password
    )

    client.connect(
        host=mqtt.host,
        port=mqtt.port,
        keepalive=mqtt.keepalive,
        # bind_address=mqtt.bind_address,
    )

    client.loop_start()

    rospy.spin()


if __name__ == "__main__":
    main()
