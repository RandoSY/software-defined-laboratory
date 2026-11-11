try:
    import utime as time
except ImportError:
    import time


class SHTC3:
    """Minimal SHTC3 temperature/humidity driver for MicroPython I2C.

    Uses wake (0x3517) and temperature-first, no-clock-stretch measurement
    (0x7866), matching the PicoBricks/MicroBlocks reference behavior.
    """
    ADDRESS = 0x70

    def __init__(self, i2c, address=ADDRESS):
        self.i2c = i2c
        self.address = int(address)

    @staticmethod
    def _crc_ok(b1, b2, crc_byte):
        crc = 0xFF
        for b in (b1, b2):
            crc ^= b
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc == crc_byte

    def _cmd(self, value):
        self.i2c.writeto(self.address, bytes(((value >> 8) & 0xFF, value & 0xFF)))

    def present(self):
        try:
            return self.address in self.i2c.scan()
        except Exception:
            return False

    def read(self):
        self._cmd(0x3517)  # wake
        # Small wake delay. Datasheet-class implementations typically need <1 ms.
        if hasattr(time, "sleep_us"):
            time.sleep_us(300)
        else:
            time.sleep(0.0003)
        self._cmd(0x7866)  # temp first, normal power, no clock stretching
        if hasattr(time, "sleep_ms"):
            time.sleep_ms(13)
        else:
            time.sleep(0.013)
        data = self.i2c.readfrom(self.address, 6)
        if len(data) != 6:
            raise OSError("SHTC3 short read")
        if not self._crc_ok(data[0], data[1], data[2]):
            raise OSError("SHTC3 temperature CRC failed")
        if not self._crc_ok(data[3], data[4], data[5]):
            raise OSError("SHTC3 humidity CRC failed")
        raw_t = (data[0] << 8) | data[1]
        raw_h = (data[3] << 8) | data[4]
        temp_c = -45.0 + 175.0 * raw_t / 65535.0
        humidity = 100.0 * raw_h / 65535.0
        return {
            "temperature_c": temp_c,
            "humidity_percent": humidity,
            "sensor": "SHTC3",
        }
