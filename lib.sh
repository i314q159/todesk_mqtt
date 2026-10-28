#!/usr/bin/bash

sudo apt install -y python3-pip

pip install paho-mqtt -i https://mirrors.cernet.edu.cn/pypi/web/simple
pip install tomli -i https://mirrors.cernet.edu.cn/pypi/web/simple
pip install netifaces -i https://mirrors.cernet.edu.cn/pypi/web/simple
