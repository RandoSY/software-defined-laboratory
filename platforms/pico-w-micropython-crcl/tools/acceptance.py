#!/usr/bin/env python3
import argparse
from sdl_client import SDLClient

TESTS = [
    ("PING", {}),
    ("INFO", {}),
    ("DEV.LIST", {}),
    ("I2C.SCAN", {}),
    ("CAP.LIST", {}),
    ("PKG.LIST", {}),
    ("APP.STATUS", {}),
    ("CRCL.STATUS", {}),
]

def ok(lines):
    return any(line.startswith("RSP ") and " OK" in line for line in lines) and not any(" ERR " in line for line in lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("host")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token", default="")
    ns = ap.parse_args()

    failures = 0
    with SDLClient(ns.host, ns.port, ns.token) as c:
        for verb, fields in TESTS:
            try:
                lines = c.command(verb, **fields)
                passed = ok(lines)
            except Exception as exc:
                lines = [str(exc)]
                passed = False
            print(("%-12s %s" % (verb, "PASS" if passed else "FAIL")))
            if not passed:
                failures += 1
                for line in lines:
                    print("   ", line)

    if failures:
        raise SystemExit("%d acceptance checks failed" % failures)
    print("PASS: core SDL/CRCL acceptance suite")

if __name__ == "__main__":
    main()
