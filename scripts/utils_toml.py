import os
import sys
from dataclasses import dataclass
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


# TODO - 测试多网卡设备
@dataclass
class MqttConfig:
    dev_id: str

    user: str
    password: str

    host: str
    port: int
    keepalive: int
    # bind_address: str
    # bind_port: int


@dataclass
class AppConfig:
    mqtt: MqttConfig


def load_toml(cfg_path: str) -> Optional[AppConfig]:
    with open(cfg_path, "rb") as f:
        raw = tomllib.load(f)

    mqtt_raw = raw.get("mqtt", {})
    mqtt_cfg = MqttConfig(
        dev_id=str(mqtt_raw.get("dev_id", "")).strip(),
        user=str(mqtt_raw.get("user", "")).strip(),
        password=str(mqtt_raw.get("pass", "")).strip(),
        host=str(mqtt_raw.get("host", "")).strip(),
        port=int(mqtt_raw.get("port", 8883)),
        keepalive=int(mqtt_raw.get("keepalive", 60)),
        # bind_address=str(mqtt_raw.get("bind_address", "")).strip(),
        # bind_port=int(mqtt_raw.get("bind_port", 8888)),
    )
    return AppConfig(mqtt=mqtt_cfg)
