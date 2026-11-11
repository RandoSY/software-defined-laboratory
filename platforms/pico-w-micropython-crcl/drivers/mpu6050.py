import struct

class MPU6050:
    ADDRESS = 0x68
    WHO_AM_I = 0x75
    PWR_MGMT_1 = 0x6B
    ACCEL_XOUT_H = 0x3B

    def __init__(self, i2c, address=0x68):
        self.i2c = i2c
        self.address = int(address)

    def present(self):
        try:
            return self.i2c.readfrom_mem(self.address, self.WHO_AM_I, 1)[0] in (0x68, 0x69)
        except Exception:
            return False

    def wake(self):
        self.i2c.writeto_mem(self.address, self.PWR_MGMT_1, b"\x00")

    def read_raw(self):
        data = self.i2c.readfrom_mem(self.address, self.ACCEL_XOUT_H, 14)
        vals = struct.unpack(">hhhhhhh", data)
        ax, ay, az, temp, gx, gy, gz = vals
        return {
            "ax_raw": ax, "ay_raw": ay, "az_raw": az,
            "gx_raw": gx, "gy_raw": gy, "gz_raw": gz,
            "temp_raw": temp,
        }

    def read(self):
        r = self.read_raw()
        return {
            "accel_x_g": r["ax_raw"] / 16384.0,
            "accel_y_g": r["ay_raw"] / 16384.0,
            "accel_z_g": r["az_raw"] / 16384.0,
            "gyro_x_dps": r["gx_raw"] / 131.0,
            "gyro_y_dps": r["gy_raw"] / 131.0,
            "gyro_z_dps": r["gz_raw"] / 131.0,
            "temperature_c": r["temp_raw"] / 340.0 + 36.53,
        }
