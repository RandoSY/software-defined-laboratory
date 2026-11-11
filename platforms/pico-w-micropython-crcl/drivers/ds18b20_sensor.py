try:
    import utime as time
except ImportError:
    import time

class DS18B20Sensor:
    def __init__(self, pin):
        from machine import Pin
        import onewire, ds18x20
        self.bus = ds18x20.DS18X20(onewire.OneWire(Pin(pin)))
        self.roms = self.bus.scan()
        self.started_ms = None

    def scan(self):
        self.roms = self.bus.scan()
        return self.roms

    def start(self):
        if not self.roms:
            self.scan()
        if not self.roms:
            raise OSError("no DS18B20 found")
        self.bus.convert_temp()
        if hasattr(time, "ticks_ms"):
            self.started_ms = time.ticks_ms()
        else:
            self.started_ms = int(time.time() * 1000)
        return len(self.roms)

    def ready(self):
        if self.started_ms is None:
            return False
        now = time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)
        diff = time.ticks_diff(now, self.started_ms) if hasattr(time, "ticks_diff") else now - self.started_ms
        return diff >= 750

    def read(self, index=0, blocking=True):
        if not self.roms:
            self.scan()
        if not self.roms:
            raise OSError("no DS18B20 found")
        if self.started_ms is None:
            self.start()
        if not self.ready():
            if not blocking:
                raise OSError("conversion not ready")
            remain = 760
            if hasattr(time, "sleep_ms"):
                time.sleep_ms(remain)
            else:
                time.sleep(remain / 1000.0)
        temp = self.bus.read_temp(self.roms[int(index)])
        self.started_ms = None
        return float(temp)
