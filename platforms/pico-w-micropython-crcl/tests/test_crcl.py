import sys, tempfile, shutil, os, base64, binascii, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sdl.app_manager import AppManager
from sdl.capabilities import CapabilityRegistry
from sdl.crcl import CRCLManager

class FakeDevices:
    def has(self, name): return False
    def read(self, name): raise KeyError(name)
    def write(self, name, value): raise KeyError(name)

class FakeLab:
    def __init__(self): self.devices = FakeDevices()

def cfg(base):
    return {
        "crcl": {
            "active_path": os.path.join(base, "apps", "crcl_app.py"),
            "backup_path": os.path.join(base, "apps", "crcl_app.py.bak"),
            "stage_path": os.path.join(base, "staging", "crcl_app.py.part"),
            "journal_path": os.path.join(base, "staging", "crcl_journal.json"),
            "max_bytes": 131072,
            "chunk_max_decoded": 384,
        }
    }

APP1 = b"""state=1\ndef health(ctx): return True\ndef setup(ctx): pass\ndef tick(ctx): pass\n"""
APP2 = b"""state=2\ndef health(ctx): return True\ndef setup(ctx): pass\ndef tick(ctx): pass\n"""
APP_BAD_HEALTH = b"""state=99\ndef health(ctx): return False\ndef setup(ctx): pass\ndef tick(ctx): pass\n"""
APP_BAD_SYNTAX = b"def broken(:\n    pass\n"

def upload(crcl, data):
    crc = binascii.crc32(data) & 0xffffffff
    sha = hashlib.sha256(data).hexdigest().upper()
    crcl.begin(len(data), "%08X" % crc, sha)
    for seq, pos in enumerate(range(0, len(data), 17)):
        crcl.data(seq, base64.b64encode(data[pos:pos+17]).decode())
    crcl.end()

def main():
    base = tempfile.mkdtemp(prefix="crcltest-")
    try:
        c = cfg(base)
        Path(c["crcl"]["active_path"]).parent.mkdir(parents=True)
        Path(c["crcl"]["stage_path"]).parent.mkdir(parents=True)
        Path(c["crcl"]["active_path"]).write_bytes(APP1)

        app = AppManager(c, FakeLab(), CapabilityRegistry())
        assert app.load(start=True)
        assert app.namespace["state"] == 1

        crcl = CRCLManager(c, app)
        upload(crcl, APP2)
        st = crcl.install()
        assert st["running"]
        assert app.namespace["state"] == 2
        assert Path(c["crcl"]["backup_path"]).exists()

        st = crcl.rollback()
        assert st["running"]
        assert app.namespace["state"] == 1

        # Bad checksum must never verify.
        crcl.begin(len(APP2), "00000000", None)
        crcl.data(0, base64.b64encode(APP2).decode())
        try:
            crcl.end()
            raise AssertionError("CRC mismatch not detected")
        except Exception:
            pass
        crcl.abort()

        # Syntax failure must be rejected before promotion.
        crc = binascii.crc32(APP_BAD_SYNTAX) & 0xffffffff
        sha = hashlib.sha256(APP_BAD_SYNTAX).hexdigest().upper()
        crcl.begin(len(APP_BAD_SYNTAX), "%08X" % crc, sha)
        crcl.data(0, base64.b64encode(APP_BAD_SYNTAX).decode())
        try:
            crcl.end()
            raise AssertionError("syntax error not detected")
        except Exception:
            pass
        crcl.abort()
        assert app.namespace["state"] == 1

        # A candidate that compiles but fails health() must roll back.
        upload(crcl, APP_BAD_HEALTH)
        try:
            crcl.install()
            raise AssertionError("bad health app installed")
        except Exception:
            pass
        assert app.namespace["state"] == 1
        assert app.running

        print("PASS test_crcl")
    finally:
        shutil.rmtree(base, ignore_errors=True)

if __name__ == "__main__":
    main()
