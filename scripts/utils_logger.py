import os

import utils_path


def init_log_dir():
    log_path = utils_path.get_log_path(utils_path.get_pkg_path())
    os.makedirs(log_path, exist_ok=True)

    return log_path
