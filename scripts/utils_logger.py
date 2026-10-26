import os
import time
import logging
import threading
from logging.handlers import TimedRotatingFileHandler

import utils_path

LOGGER_NAME = "todesk_mqtt"
LOG_FILE_NAME = "todesk_mqtt.log"
LOG_LEVEL = logging.INFO

LOG_WHEN = "midnight"
LOG_BACKUP_COUNT = 30
LOG_ENCODING = "utf-8"
LOG_DELAY = False

WATCHDOG_INTERVAL = 3600.0
WATCHDOG_THREAD_NAME = "todesk-log-rollover-watchdog"

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

_logger = None
log = None
_watchdog_started = False


def _rollover_watchdog(handler, interval=WATCHDOG_INTERVAL):
    def _watch():
        while True:
            try:
                handler.acquire()
                try:
                    if time.time() >= handler.rolloverAt:
                        handler.doRollover()
                finally:
                    handler.release()
            except Exception:
                pass
            time.sleep(interval)

    t = threading.Thread(target=_watch, name=WATCHDOG_THREAD_NAME, daemon=True)
    t.start()
    return t


def init_log_dir():
    global _logger, log, _watchdog_started
    if _logger is not None:
        return _logger

    log_path = utils_path.get_log_path(utils_path.get_pkg_path())
    os.makedirs(log_path, exist_ok=True)
    log_file = os.path.join(log_path, LOG_FILE_NAME)

    _logger = logging.getLogger(LOGGER_NAME)
    _logger.setLevel(LOG_LEVEL)

    for h in list(_logger.handlers):
        try:
            h.close()
        except Exception:
            pass
    _logger.handlers.clear()
    _logger.propagate = False

    fh = TimedRotatingFileHandler(
        log_file,
        when=LOG_WHEN,
        backupCount=LOG_BACKUP_COUNT,
        encoding=LOG_ENCODING,
        delay=LOG_DELAY,
    )
    fmt = logging.Formatter(LOG_FORMAT)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)

    _logger.addHandler(fh)
    _logger.addHandler(sh)

    if not _watchdog_started:
        _rollover_watchdog(fh)
        _watchdog_started = True

    log = _logger
    return _logger


def log_flush():
    if log is None:
        return
    for h in log.handlers:
        try:
            h.flush()
        except Exception:
            pass
