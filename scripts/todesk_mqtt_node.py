#!/usr/bin/python3

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# import scripts.utils_toml as utils_toml
# import scripts.utils_mqtt as utils_mqtt

import utils_toml
import utils_mqtt
import utils_path
import utils_logger
import utils_network

import rospy
import rospkg


def main():
    rospy.init_node("todesk_mqtt_node")

    log = utils_logger.init_log_dir()

    cfg_path = utils_path.get_cfg_path(utils_path.get_pkg_path())

    cfg = utils_toml.load_toml(cfg_path)
    mqtt = cfg.mqtt

    iface_name, local_ip = utils_network.find_192_168_1_x_ip()

    if local_ip == None:
        rospy.logerr("192.168.1.x not found, node exit")
        sys.exit(1)

    client = utils_mqtt.init_client(
        dev_id=mqtt.dev_id, user=mqtt.user, password=mqtt.password
    )

    client.connect(
        host=mqtt.host,
        port=mqtt.port,
        keepalive=mqtt.keepalive,
        bind_address=local_ip,
    )

    client.loop_start()

    rospy.spin()


if __name__ == "__main__":
    main()
