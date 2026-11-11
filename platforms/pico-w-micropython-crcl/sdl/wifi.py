from sdl.util import sleep_ms, ticks_ms, ticks_diff


class WiFiManager:
    def __init__(self, config):
        self.config = config
        self.wlan = None
        self.ip = None
        self.error = None

    def connect(self):
        ssid = self.config["wifi"].get("ssid", "")
        if not ssid:
            self.error = "SSID not configured"
            return False
        try:
            import network
            iface = getattr(network, "STA_IF", None)
            if iface is None:
                iface = network.WLAN.IF_STA
            wlan = network.WLAN(iface)
            wlan.active(True)
            hostname = self.config["wifi"].get("hostname")
            if hostname:
                try:
                    wlan.config(hostname=hostname)
                except Exception:
                    try:
                        network.hostname(hostname)
                    except Exception:
                        pass
            if not wlan.isconnected():
                wlan.connect(ssid, self.config["wifi"].get("password", ""))
                start = ticks_ms()
                timeout = int(self.config["wifi"].get("connect_timeout_s", 20)) * 1000
                while not wlan.isconnected():
                    if ticks_diff(ticks_ms(), start) >= timeout:
                        try:
                            wlan.disconnect()
                        except Exception:
                            pass
                        self.error = "Wi-Fi connect timeout status=%s" % wlan.status()
                        self.wlan = wlan
                        return False
                    sleep_ms(100)
            self.wlan = wlan
            try:
                cfg = wlan.ifconfig()
                self.ip = cfg[0]
            except Exception:
                try:
                    addr = wlan.ipconfig("addr4")
                    self.ip = addr[0] if isinstance(addr, tuple) else str(addr).split("/")[0]
                except Exception:
                    self.ip = "unknown"
            self.error = None
            return True
        except Exception as exc:
            self.error = str(exc)
            return False

    def status(self):
        return {
            "connected": bool(self.wlan and self.wlan.isconnected()),
            "ip": self.ip or "",
            "error": self.error or "",
        }
