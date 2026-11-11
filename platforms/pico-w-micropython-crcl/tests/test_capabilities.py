import sys, tempfile, shutil, os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sdl.capabilities import CapabilityRegistry, CapabilityManager

class Devices:
    def has(self, name): return name == "temp1"
class Lab:
    devices = Devices()

def main():
    base = tempfile.mkdtemp(prefix="captest-")
    try:
        p = Path(base)/"x"
        p.mkdir()
        (p/"READY").write_text("ready\n")
        (p/"manifest.json").write_text(json.dumps({
            "apiVersion":"1.0.0","id":"x","version":"1",
            "provides":["hello"],"requires":{"sensors":[]}
        }))
        (p/"module.py").write_text(
            "def register(registry, lab):\n"
            "    registry.register('hello', lambda args: {'value':'world'})\n"
        )
        reg = CapabilityRegistry()
        mgr = CapabilityManager(base, reg, Lab())
        mgr.load_all()
        assert reg.names() == ["hello"]
        assert reg.call("hello", {})["value"] == "world"
        assert mgr.packages["x"]["status"] == "active"
        print("PASS test_capabilities")
    finally:
        shutil.rmtree(base, ignore_errors=True)

if __name__ == "__main__":
    main()
