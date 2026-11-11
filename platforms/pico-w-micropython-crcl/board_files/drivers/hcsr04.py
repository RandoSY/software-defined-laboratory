try:
    import utime as time
except ImportError:
    import time

class HCSR04:
    def __init__(self, trig_pin, echo_pin, timeout_us=40000):
        from machine import Pin
        self.trig = Pin(trig_pin, Pin.OUT, value=0)
        self.echo = Pin(echo_pin, Pin.IN)
        self.timeout_us = int(timeout_us)

    def pulse_us(self):
        from machine import time_pulse_us
        self.trig.value(0)
        if hasattr(time, "sleep_us"):
            time.sleep_us(2)
        self.trig.value(1)
        if hasattr(time, "sleep_us"):
            time.sleep_us(10)
        else:
            time.sleep(0.000010)
        self.trig.value(0)
        t = time_pulse_us(self.echo, 1, self.timeout_us)
        if t < 0:
            raise OSError("HC-SR04 echo timeout (%d)" % t)
        return t

    def read(self, temperature_c=20.0):
        t = self.pulse_us()
        # speed of sound approximation in dry air, m/s
        c = 331.3 + 0.606 * float(temperature_c)
        mm = (t * c) / 2000.0
        return {
            "echo_us": t,
            "distance_mm": mm,
            "distance_cm": mm / 10.0,
            "temperature_comp_c": float(temperature_c),
        }
