from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "board_files"

PAIRS = [
    (ROOT / "main.py", BOARD / "main.py"),
    (ROOT / "boot.py", BOARD / "boot.py"),
    (ROOT / "config_default.py", BOARD / "config_default.py"),
]
for dirname in ("sdl", "drivers", "capabilities", "apps"):
    for src in sorted((ROOT / dirname).rglob("*")):
        if src.is_file() and "__pycache__" not in src.parts:
            rel = src.relative_to(ROOT)
            PAIRS.append((src, BOARD / rel))

def main():
    missing=[]; different=[]
    for src,dst in PAIRS:
        if not dst.exists(): missing.append(str(dst.relative_to(ROOT))); continue
        if src.read_bytes()!=dst.read_bytes(): different.append(str(src.relative_to(ROOT)))
    assert not missing, "missing board files: %s" % missing
    assert not different, "board/source mismatch: %s" % different
    print("PASS test_release_sync (%d files)" % len(PAIRS))
if __name__ == "__main__": main()
