import os

import rospy
import rospkg


def get_pkg_path():
    pkg_path = rospkg.RosPack().get_path("todesk_mqtt")
    return pkg_path


def get_cfg_path(pkg_path):
    cfg_file = os.path.join(pkg_path, "config.toml")
    return cfg_file


def get_log_path(pkg_path):
    log_path = os.path.join(pkg_path, "log")
    return log_path
