import subprocess, sys
from pathlib import Path
here = Path(__file__).resolve().parent
tests = ["test_protocol.py", "test_crcl.py", "test_crcl_powerloss.py", "test_shtc3.py", "test_capabilities.py", "test_release_sync.py"]
for t in tests:
    subprocess.check_call([sys.executable, str(here/t)])
print("PASS all desktop tests")
