import netifaces


def find_192_168_1_x_ip():
    for ifname in netifaces.interfaces():
        addrs = netifaces.ifaddresses(ifname)
        for link in addrs.get(netifaces.AF_INET, []):
            ip = link.get("addr")
            if ip and ip.startswith("192.168.1."):
                return ifname, ip
    return None, None
