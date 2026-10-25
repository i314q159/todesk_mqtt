import os
import logging
from logging.handlers import TimedRotatingFileHandler
import utils_path

_logger = None
log = None


def init_log_dir():
    global _logger, log
    if _logger is not None:
        return _logger

    log_path = utils_path.get_log_path(utils_path.get_pkg_path())
    os.makedirs(log_path, exist_ok=True)
    log_file = os.path.join(log_path, "todesk_mqtt.log")

    _logger = logging.getLogger("todesk_mqtt")
    _logger.setLevel(logging.INFO)
    _logger.handlers.clear()
    _logger.propagate = False

    fh = TimedRotatingFileHandler(
        log_file, when="midnight", backupCount=7, encoding="utf-8", delay=False
    )
    fmt = logging.Formatter("%(asctime)s | %(message)s")
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)

    _logger.addHandler(fh)
    _logger.addHandler(sh)
    log = _logger
    return _logger


def log_flush():
    for h in log.handlers:
        h.flush()
