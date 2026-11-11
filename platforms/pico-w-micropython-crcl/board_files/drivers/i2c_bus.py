class I2CBus:
    def __init__(self, bus_id=0, sda=4, scl=5, freq=400000):
        from machine import I2C, Pin
        self.bus_id = bus_id
        self.sda_pin = sda
        self.scl_pin = scl
        self.freq = freq
        self.i2c = I2C(bus_id, sda=Pin(sda), scl=Pin(scl), freq=freq)

    def scan(self):
        return list(self.i2c.scan())

    def probe(self, addr):
        return int(addr) in self.scan()

    def read8(self, addr, reg):
        return self.i2c.readfrom_mem(int(addr), int(reg), 1)[0]

    def write8(self, addr, reg, value):
        self.i2c.writeto_mem(int(addr), int(reg), bytes([int(value) & 0xff]))
        return True

    def readn(self, addr, reg, n):
        n = max(1, min(64, int(n)))
        return bytes(self.i2c.readfrom_mem(int(addr), int(reg), n))

    def writen(self, addr, reg, data):
        self.i2c.writeto_mem(int(addr), int(reg), bytes(data))
        return True
