import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sdl.protocol import parse_wire_line, human_to_wire

def main():
    r = parse_wire_line("CMD 17 DEV.READ ID=temp1 TOKEN=x")
    assert r.id == "17"
    assert r.verb == "DEV.READ"
    assert r.get("ID") == "temp1"
    assert human_to_wire("ping", "1") == "CMD 1 PING"
    assert human_to_wire("dev read temp1", "2") == "CMD 2 DEV.READ ID=temp1"
    assert human_to_wire("i2c read 68 75", "3") == "CMD 3 I2C.READ ADDR=68 REG=75 N=1"
    print("PASS test_protocol")

if __name__ == "__main__":
    main()
