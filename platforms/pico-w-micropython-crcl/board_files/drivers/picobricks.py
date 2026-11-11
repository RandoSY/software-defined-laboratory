class PicoBricks:
    """MicroPython adapter for documented PicoBricks GPIO revisions.

    Temperature/humidity is revision-aware: newer boards can expose SHTC3 on
    I2C address 0x70; older boards use DHT11 on GP11. SHTC3 is preferred when
    detected, otherwise DHT11 is used when MicroPython's dht module is present.
    """
    def __init__(self, pins, i2c=None):
        from machine import Pin, ADC, PWM
        self.Pin = Pin
        self.ADC = ADC
        self.PWM = PWM
        self.pins = pins
        self.i2c = i2c

        self.red_led = Pin(pins["picobricks_red_led"], Pin.OUT, value=0)
        self.button = Pin(pins["picobricks_button"], Pin.IN, Pin.PULL_DOWN)
        self.relay = Pin(pins["picobricks_relay"], Pin.OUT, value=0)
        self.pot = ADC(pins["picobricks_pot_adc"])
        self.ldr = ADC(pins["picobricks_ldr_adc"])
        self.buzzer = PWM(Pin(pins["picobricks_buzzer"]))
        self.buzzer.duty_u16(0)

        self.rgb = None
        try:
            import neopixel
            self.rgb = neopixel.NeoPixel(Pin(pins["picobricks_rgb"]), 1)
            self.rgb[0] = (0, 0, 0)
            self.rgb.write()
        except Exception:
            self.rgb = None

        self.shtc3 = None
        if i2c is not None:
            try:
                from drivers.shtc3_sensor import SHTC3
                candidate = SHTC3(i2c)
                if candidate.present():
                    # Read once so address presence alone does not masquerade as SHTC3.
                    candidate.read()
                    self.shtc3 = candidate
            except Exception:
                self.shtc3 = None

        self.dht = None
        if self.shtc3 is None:
            try:
                import dht
                self.dht = dht.DHT11(Pin(pins["picobricks_dht"]))
            except Exception:
                self.dht = None

    @property
    def environment_model(self):
        if self.shtc3 is not None:
            return "SHTC3"
        if self.dht is not None:
            return "DHT11"
        return None

    def read_button(self):
        return int(self.button.value())

    def set_led(self, value):
        self.red_led.value(1 if int(float(value)) else 0)
        return int(self.red_led.value())

    def set_relay(self, value):
        self.relay.value(1 if int(float(value)) else 0)
        return int(self.relay.value())

    def read_pot(self):
        raw = int(self.pot.read_u16())
        return {"raw": raw, "percent": raw * 100.0 / 65535.0}

    def read_ldr(self):
        raw = int(self.ldr.read_u16())
        return {"raw": raw, "percent": raw * 100.0 / 65535.0}

    def read_environment(self):
        if self.shtc3 is not None:
            return self.shtc3.read()
        if self.dht is not None:
            self.dht.measure()
            return {
                "temperature_c": float(self.dht.temperature()),
                "humidity_percent": float(self.dht.humidity()),
                "sensor": "DHT11",
            }
        raise OSError("PicoBricks temperature/humidity sensor unavailable")

    def read_dht(self):
        """Backward-compatible alias for v1.0 applications."""
        return self.read_environment()

    def set_rgb(self, r, g, b):
        if self.rgb is None:
            raise OSError("NeoPixel support unavailable")
        vals = (max(0,min(255,int(r))), max(0,min(255,int(g))), max(0,min(255,int(b))))
        self.rgb[0] = vals
        self.rgb.write()
        return vals

    def beep(self, hz=1000, ms=100):
        try:
            import utime as time
        except ImportError:
            import time
        self.buzzer.freq(max(20, min(20000, int(hz))))
        self.buzzer.duty_u16(32768)
        if hasattr(time, "sleep_ms"):
            time.sleep_ms(int(ms))
        else:
            time.sleep(ms / 1000.0)
        self.buzzer.duty_u16(0)
