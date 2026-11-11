# Compact MicroPython HX711 driver.
# Design informed by the widely used MIT-licensed robert-hh/hx711 implementation.
# Key safety detail: PD_SCK high pulses are protected from long interrupt latency.

try:
    import utime as time
except ImportError:
    import time

class HX711Sensor:
    def __init__(self, dout_pin, sck_pin, gain_pulses=1, ready_timeout_ms=800,
                 offset=0.0, counts_per_unit=1.0, unit="g"):
        from machine import Pin
        self.data = Pin(dout_pin, Pin.IN)
        self.clock = Pin(sck_pin, Pin.OUT, value=0)
        self.gain_pulses = int(gain_pulses)
        if self.gain_pulses not in (1, 2, 3):
            raise ValueError("gain_pulses must be 1,2,3")
        self.ready_timeout_ms = int(ready_timeout_ms)
        self.offset = float(offset)
        self.counts_per_unit = float(counts_per_unit) or 1.0
        self.unit = unit

    def is_ready(self):
        return self.data.value() == 0

    def _wait_ready(self):
        start = time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time()*1000)
        while not self.is_ready():
            now = time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time()*1000)
            dt = time.ticks_diff(now, start) if hasattr(time, "ticks_diff") else now-start
            if dt >= self.ready_timeout_ms:
                raise OSError("HX711 ready timeout")
            if hasattr(time, "sleep_ms"):
                time.sleep_ms(1)

    def read_raw(self):
        from machine import disable_irq, enable_irq
        self._wait_ready()
        value = 0
        for _ in range(24):
            state = disable_irq()
            self.clock.value(1)
            self.clock.value(0)
            enable_irq(state)
            value = (value << 1) | self.data.value()

        # Additional pulses choose next conversion channel/gain:
        # 1=A/128, 2=B/32, 3=A/64.
        for _ in range(self.gain_pulses):
            state = disable_irq()
            self.clock.value(1)
            self.clock.value(0)
            enable_irq(state)

        if value & 0x800000:
            value -= 0x1000000
        return int(value)

    def average_raw(self, samples=5):
        n = max(1, min(50, int(samples)))
        total = 0
        for _ in range(n):
            total += self.read_raw()
        return total / n

    def tare(self, samples=10):
        self.offset = self.average_raw(samples)
        return self.offset

    def units(self, samples=5):
        raw = self.average_raw(samples)
        return (raw - self.offset) / self.counts_per_unit

    def read(self, samples=1):
        raw = self.read_raw() if int(samples) <= 1 else self.average_raw(samples)
        return {
            "raw": raw,
            "offset": self.offset,
            "units": (raw - self.offset) / self.counts_per_unit,
            "unit": self.unit,
        }
