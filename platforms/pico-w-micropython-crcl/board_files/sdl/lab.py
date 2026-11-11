from sdl.devices import DeviceRegistry, LogicalDevice
from sdl.util import parse_float


class Lab:
    def __init__(self, config):
        self.config = config
        self.devices = DeviceRegistry()
        self.i2c_bus = None
        self.mpu6050 = None
        self.picobricks = None
        self.ds18b20 = None
        self.hcsr04 = None
        self.hx711 = None
        self._build()

    def _build(self):
        cfg = self.config
        pins = cfg["pins"]
        devcfg = cfg["devices"]

        if devcfg.get("enable_i2c_bus"):
            try:
                from drivers.i2c_bus import I2CBus
                self.i2c_bus = I2CBus(
                    pins["i2c_id"], pins["i2c_sda"], pins["i2c_scl"], pins["i2c_freq"]
                )
                self.devices.register(LogicalDevice(
                    "i2c0", "read", "I2C-BUS", "hardware",
                    read_fn=lambda: {"addresses": ",".join("0x%02X" % a for a in self.i2c_bus.scan())}
                ))
            except Exception as exc:
                print("WARN,I2C_INIT,%s" % exc)

        if devcfg.get("enable_picobricks"):
            try:
                from drivers.picobricks import PicoBricks
                self.picobricks = PicoBricks(pins, self.i2c_bus.i2c if self.i2c_bus else None)
                pb = self.picobricks
                self.devices.register(LogicalDevice(
                    "pb.button", "read", "PicoBricks-Button", "hardware",
                    read_fn=lambda: {"value": pb.read_button()}
                ))
                self.devices.register(LogicalDevice(
                    "pb.led", "rw", "PicoBricks-RedLED", "hardware",
                    read_fn=lambda: {"value": int(pb.red_led.value())},
                    write_fn=lambda v: {"value": pb.set_led(v)}
                ))
                self.devices.register(LogicalDevice(
                    "pb.relay", "rw", "PicoBricks-Relay", "hardware",
                    read_fn=lambda: {"value": int(pb.relay.value())},
                    write_fn=lambda v: {"value": pb.set_relay(v)}
                ))
                if pb.rgb is not None:
                    def set_rgb_value(v):
                        parts = str(v).split(",")
                        if len(parts) != 3:
                            raise ValueError("RGB value must be r,g,b")
                        vals = pb.set_rgb(int(parts[0]), int(parts[1]), int(parts[2]))
                        return {"rgb": "%d,%d,%d" % vals}
                    self.devices.register(LogicalDevice(
                        "pb.rgb", "write", "PicoBricks-RGB", "hardware",
                        write_fn=set_rgb_value
                    ))
                def beep_value(v):
                    parts = str(v).split(",")
                    hz = int(parts[0]) if parts and parts[0] else 1000
                    ms = int(parts[1]) if len(parts) > 1 else 100
                    pb.beep(hz, ms)
                    return {"hz": hz, "ms": ms}
                self.devices.register(LogicalDevice(
                    "pb.buzzer", "write", "PicoBricks-Buzzer", "hardware",
                    write_fn=beep_value
                ))
                self.devices.register(LogicalDevice(
                    "pb.pot", "read", "PicoBricks-Potentiometer", "hardware",
                    read_fn=pb.read_pot
                ))
                self.devices.register(LogicalDevice(
                    "pb.ldr", "read", "PicoBricks-LDR", "hardware",
                    read_fn=pb.read_ldr
                ))
                if pb.environment_model is not None:
                    self.devices.register(LogicalDevice(
                        "pb.env", "read", "PicoBricks-%s" % pb.environment_model, "hardware",
                        read_fn=pb.read_environment,
                        meta={"role":"environment_temperature_humidity"}
                    ))
                    if pb.shtc3 is not None:
                        self.devices.register(LogicalDevice(
                            "pb.shtc3", "read", "PicoBricks-SHTC3", "hardware",
                            read_fn=pb.read_environment
                        ))
                    elif pb.dht is not None:
                        self.devices.register(LogicalDevice(
                            "pb.dht", "read", "PicoBricks-DHT11", "hardware",
                            read_fn=pb.read_environment
                        ))
            except Exception as exc:
                print("WARN,PICOBRICKS_INIT,%s" % exc)

        if devcfg.get("enable_internal_temp"):
            try:
                from machine import ADC
                adc = ADC(4)
                def cpu_temp():
                    # RP2040 internal sensor conversion from Raspberry Pi documentation.
                    raw = adc.read_u16()
                    voltage = raw * 3.3 / 65535.0
                    return {"temperature_c": 27.0 - (voltage - 0.706) / 0.001721}
                self.devices.register(LogicalDevice(
                    "cpu_temp", "read", "RP2040-InternalTemperature", "hardware", read_fn=cpu_temp
                ))
            except Exception as exc:
                print("WARN,CPU_TEMP_INIT,%s" % exc)

        if devcfg.get("enable_ds18b20") and pins.get("ds18b20_dq") is not None:
            try:
                from drivers.ds18b20_sensor import DS18B20Sensor
                self.ds18b20 = DS18B20Sensor(pins["ds18b20_dq"])
                def read_temp():
                    t = self.ds18b20.read()
                    return {"temperature_c": t, "temperature_f": t * 9.0 / 5.0 + 32.0}
                self.devices.register(LogicalDevice(
                    "temp1", "read", "DS18B20", "hardware", read_fn=read_temp
                ))
            except Exception as exc:
                print("WARN,DS18B20_INIT,%s" % exc)

        # Stable logical environmental role: prefer DS18B20 when explicitly wired;
        # otherwise use the PicoBricks environmental sensor (SHTC3 on newer boards,
        # DHT11 on older revisions).
        if (not self.devices.has("temp1") and self.picobricks is not None
                and self.picobricks.environment_model is not None):
            def read_temp_from_picobricks():
                d = self.picobricks.read_environment()
                return {
                    "temperature_c": d["temperature_c"],
                    "temperature_f": d["temperature_c"] * 9.0 / 5.0 + 32.0,
                    "humidity_percent": d["humidity_percent"],
                    "sensor": d.get("sensor", self.picobricks.environment_model),
                }
            try:
                self.devices.register(LogicalDevice(
                    "temp1", "read", self.picobricks.environment_model, "hardware",
                    read_fn=read_temp_from_picobricks,
                    meta={"role":"environment_temperature"}
                ))
            except Exception:
                pass

        if devcfg.get("enable_hcsr04") and pins.get("hcsr04_trig") is not None and pins.get("hcsr04_echo") is not None:
            try:
                from drivers.hcsr04 import HCSR04
                self.hcsr04 = HCSR04(pins["hcsr04_trig"], pins["hcsr04_echo"])
                def read_dist():
                    temp = 20.0
                    if self.devices.has("temp1"):
                        try:
                            temp = float(self.devices.read("temp1")["temperature_c"])
                        except Exception:
                            pass
                    return self.hcsr04.read(temp)
                self.devices.register(LogicalDevice(
                    "distance1", "read", "HC-SR04", "hardware", read_fn=read_dist
                ))
            except Exception as exc:
                print("WARN,HCSR04_INIT,%s" % exc)

        if devcfg.get("enable_hx711") and pins.get("hx711_dout") is not None and pins.get("hx711_sck") is not None:
            try:
                from drivers.hx711_sensor import HX711Sensor
                hc = cfg["hx711"]
                self.hx711 = HX711Sensor(
                    pins["hx711_dout"], pins["hx711_sck"],
                    gain_pulses=hc["gain_pulses"],
                    ready_timeout_ms=hc["ready_timeout_ms"],
                    offset=hc["offset"],
                    counts_per_unit=hc["raw_count_per_unit"],
                    unit=hc["unit"],
                )
                self.devices.register(LogicalDevice(
                    "mass1", "read", "HX711", "hardware",
                    read_fn=lambda: self.hx711.read(samples=3)
                ))
            except Exception as exc:
                print("WARN,HX711_INIT,%s" % exc)

        if devcfg.get("enable_mpu6050_autodetect") and self.i2c_bus:
            try:
                from drivers.mpu6050 import MPU6050
                candidate = MPU6050(self.i2c_bus.i2c, 0x68)
                if candidate.present():
                    candidate.wake()
                    self.mpu6050 = candidate
                    self.devices.register(LogicalDevice(
                        "imu1", "read", "MPU6050", "hardware", read_fn=candidate.read
                    ))
            except Exception as exc:
                print("WARN,MPU6050_INIT,%s" % exc)

    def summary(self):
        return [{"id":d.id, "direction":d.direction, "model":d.model, "backend":d.backend}
                for d in self.devices.list()]
