import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from drivers.shtc3_sensor import SHTC3


def crc(b1,b2):
    c=0xFF
    for b in (b1,b2):
        c ^= b
        for _ in range(8):
            c = (((c<<1)^0x31)&0xFF) if (c&0x80) else ((c<<1)&0xFF)
    return c

class FakeI2C:
    def __init__(self, raw_t, raw_h):
        self.raw_t=raw_t; self.raw_h=raw_h; self.commands=[]
    def scan(self): return [0x3C,0x70]
    def writeto(self, addr, data): self.commands.append((addr,bytes(data)))
    def readfrom(self, addr, n):
        t1=(self.raw_t>>8)&255; t2=self.raw_t&255
        h1=(self.raw_h>>8)&255; h2=self.raw_h&255
        return bytes((t1,t2,crc(t1,t2),h1,h2,crc(h1,h2)))

def main():
    i2c=FakeI2C(32768,32768)
    s=SHTC3(i2c)
    assert s.present()
    d=s.read()
    assert abs(d["temperature_c"]-42.5013) < 0.02
    assert abs(d["humidity_percent"]-50.0008) < 0.02
    assert i2c.commands[0][1] == bytes((0x35,0x17))
    assert i2c.commands[1][1] == bytes((0x78,0x66))
    print("PASS test_shtc3")
if __name__ == "__main__": main()
