import sys, tempfile, shutil, os, base64, binascii
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sdl.app_manager import AppManager
from sdl.capabilities import CapabilityRegistry
from sdl.crcl import CRCLManager
from sdl.durable import DualSlotJournal, write_json_marker

class FakeDevices:
    def has(self, name): return False
    def read(self, name): raise KeyError(name)
    def write(self, name, value): raise KeyError(name)
class FakeLab:
    def __init__(self): self.devices = FakeDevices()

def cfg(base):
    return {"crcl": {
        "active_path": os.path.join(base, "apps", "crcl_app.py"),
        "backup_path": os.path.join(base, "apps", "crcl_app.py.bak"),
        "stage_path": os.path.join(base, "staging", "crcl_app.py.part"),
        "journal_path": os.path.join(base, "staging", "crcl_journal.json"),
        "install_marker_path": os.path.join(base, "staging", "crcl_install.json"),
        "previous_backup_path": os.path.join(base, "apps", "crcl_app.py.bak.previous"),
        "recovery_failed_path": os.path.join(base, "staging", "crcl_app.py.recovery_failed"),
        "max_bytes": 131072,
        "chunk_max_decoded": 384,
    }}

APP1 = b"state=1\ndef health(ctx): return True\ndef setup(ctx): pass\ndef tick(ctx): pass\n"
APP2 = b"state=2\ndef health(ctx): return True\ndef setup(ctx): pass\ndef tick(ctx): pass\n"

def new_env(base):
    c = cfg(base)
    Path(c["crcl"]["active_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(c["crcl"]["stage_path"]).parent.mkdir(parents=True, exist_ok=True)
    app = AppManager(c, FakeLab(), CapabilityRegistry())
    return c, app

def test_full_pending_chunk_recovery():
    base=tempfile.mkdtemp(prefix="crcl-full-")
    try:
        c, app = new_env(base)
        crcl=CRCLManager(c, app)
        data=b"hello-power-loss"
        crcl.begin(len(data), "%08X" % (binascii.crc32(data)&0xffffffff))
        crcl.state["pending"]={"seq":0,"length":len(data),"crc32":"%08X"%(binascii.crc32(data)&0xffffffff)}
        crcl._save()
        with open(c["crcl"]["stage_path"],"ab") as f: f.write(data)
        # Simulated reset before committed-journal update.
        crcl2=CRCLManager(c, app)
        assert crcl2.state["received"]==len(data)
        assert crcl2.state["next_seq"]==1
        assert not crcl2.state.get("pending")
    finally:
        shutil.rmtree(base, ignore_errors=True)

def test_partial_pending_chunk_recovery():
    base=tempfile.mkdtemp(prefix="crcl-part-")
    try:
        c, app = new_env(base)
        crcl=CRCLManager(c, app)
        data=b"0123456789ABCDEF"
        crcl.begin(len(data), "%08X" % (binascii.crc32(data)&0xffffffff))
        crcl.state["pending"]={"seq":0,"length":len(data),"crc32":"%08X"%(binascii.crc32(data)&0xffffffff)}
        crcl._save()
        with open(c["crcl"]["stage_path"],"ab") as f: f.write(data[:7])
        crcl2=CRCLManager(c, app)
        assert crcl2.state["received"]==0
        assert crcl2.state["next_seq"]==0
        assert os.path.getsize(c["crcl"]["stage_path"])==0
        assert crcl2.state.get("recovery")=="partial_chunk_discarded"
    finally:
        shutil.rmtree(base, ignore_errors=True)

def test_dual_slot_survives_latest_corruption():
    base=tempfile.mkdtemp(prefix="crcl-journal-")
    try:
        path=os.path.join(base,"j")
        j=DualSlotJournal(path)
        j.write({"n":1})
        j.write({"n":2})
        latest=j.paths[j.generation & 1]
        Path(latest).write_bytes(b"corrupt")
        j2=DualSlotJournal(path)
        assert j2.read()["n"]==1
    finally:
        shutil.rmtree(base, ignore_errors=True)

def test_install_marker_rolls_back_promoted_candidate():
    base=tempfile.mkdtemp(prefix="crcl-install-")
    try:
        c=cfg(base); cc=c["crcl"]
        Path(cc["active_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(cc["stage_path"]).parent.mkdir(parents=True, exist_ok=True)
        # State after active->backup and stage->active but before health/commit.
        Path(cc["active_path"]).write_bytes(APP2)
        Path(cc["backup_path"]).write_bytes(APP1)
        write_json_marker(cc["install_marker_path"], {"version":1,"had_active":True,"had_prior_backup":False})
        app=AppManager(c, FakeLab(), CapabilityRegistry())
        assert Path(cc["active_path"]).read_bytes()==APP1
        assert Path(cc["recovery_failed_path"]).read_bytes()==APP2
        assert not Path(cc["install_marker_path"]).exists()
        assert app.load(start=True)
        assert app.namespace["state"]==1
    finally:
        shutil.rmtree(base, ignore_errors=True)

def test_install_marker_preserves_old_active_before_promotion():
    base=tempfile.mkdtemp(prefix="crcl-prepromote-")
    try:
        c=cfg(base); cc=c["crcl"]
        Path(cc["active_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(cc["stage_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(cc["active_path"]).write_bytes(APP1)
        Path(cc["stage_path"]).write_bytes(APP2)
        write_json_marker(cc["install_marker_path"], {"version":1,"had_active":True,"had_prior_backup":False})
        AppManager(c, FakeLab(), CapabilityRegistry())
        assert Path(cc["active_path"]).read_bytes()==APP1
        assert Path(cc["stage_path"]).read_bytes()==APP2
        assert not Path(cc["install_marker_path"]).exists()
    finally:
        shutil.rmtree(base, ignore_errors=True)

def main():
    test_full_pending_chunk_recovery()
    test_partial_pending_chunk_recovery()
    test_dual_slot_survives_latest_corruption()
    test_install_marker_rolls_back_promoted_candidate()
    test_install_marker_preserves_old_active_before_promotion()
    print("PASS test_crcl_powerloss")

if __name__ == "__main__": main()
