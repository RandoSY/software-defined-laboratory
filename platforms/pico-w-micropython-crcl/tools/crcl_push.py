#!/usr/bin/env python3
"""Transactional CRCL application uploader for Pico W SDL/CRCL Reference Node.

No uncertain DATA command is silently retried. If transport is lost after a chunk may
have arrived, reconnect and rerun with --resume. The target's durable journal reports
the next accepted sequence number and byte offset.
"""
import argparse
import base64
import binascii
import hashlib
from pathlib import Path

from sdl_client import SDLClient


def require_ok(lines, step):
    for line in lines:
        if line.startswith("RSP ") and " ERR " in line:
            raise RuntimeError("%s failed: %s" % (step, line))
    return lines


def parse_dat(lines, record="CRCL"):
    prefix = "DAT "
    for line in lines:
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "DAT" and parts[2] == record:
            out = {}
            for tok in parts[3:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    out[k] = v
            return out
    return {}


def push(host, filename, port=8765, token="", chunk=240, install=True, resume=False):
    data = Path(filename).read_bytes()
    crc = binascii.crc32(data) & 0xffffffff
    crc_hex = "%08X" % crc
    sha = hashlib.sha256(data).hexdigest().upper()

    print("File:", filename)
    print("Bytes:", len(data))
    print("CRC32:", crc_hex)
    print("SHA256:", sha)

    with SDLClient(host, port, token, timeout=10.0) as c:
        seq = 0
        sent = 0

        if resume:
            status_lines = require_ok(c.command("CRCL.STATUS"), "STATUS")
            st = parse_dat(status_lines)
            if st.get("state") != "receiving":
                raise RuntimeError("target has no resumable receiving session")
            if int(st.get("size", -1)) != len(data) or st.get("crc32", "").upper() != crc_hex:
                raise RuntimeError("target staging metadata does not match local file")
            if st.get("sha256") and st.get("sha256", "").upper() != sha:
                raise RuntimeError("target SHA256 metadata does not match local file")
            seq = int(st.get("next_seq", 0))
            sent = int(st.get("received", 0))
            if sent < 0 or sent > len(data):
                raise RuntimeError("target reports invalid received offset")
            print("Resuming at sequence %d, byte %d" % (seq, sent))
        else:
            lines = c.command("CRCL.BEGIN", SIZE=len(data), CRC32=crc_hex, SHA256=sha)
            require_ok(lines, "BEGIN")

        pos = sent
        try:
            while pos < len(data):
                block = data[pos:pos+chunk]
                b64 = base64.b64encode(block).decode("ascii")
                lines = c.command("CRCL.DATA", SEQ=seq, B64=b64)
                require_ok(lines, "DATA %d" % seq)
                pos += len(block)
                print("\rDATA %d  %d/%d bytes" % (seq, pos, len(data)), end="", flush=True)
                seq += 1
        except Exception:
            print()
            print("Transfer stopped. No uncertain DATA chunk was retried.")
            print("After connectivity is restored, rerun the same command with --resume.")
            raise
        print()

        lines = c.command("CRCL.END")
        require_ok(lines, "END")
        for line in lines:
            print(line)

        if install:
            lines = c.command("CRCL.INSTALL")
            require_ok(lines, "INSTALL")
            for line in lines:
                print(line)

            lines = c.command("APP.STATUS")
            require_ok(lines, "APP.STATUS")
            for line in lines:
                print(line)


def main():
    ap = argparse.ArgumentParser(description="Push and transactionally install a CRCL app")
    ap.add_argument("host")
    ap.add_argument("file")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token", default="")
    ap.add_argument("--chunk", type=int, default=240,
                    help="decoded bytes per DATA command; keep <= target chunk_max_decoded")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--resume", action="store_true",
                    help="resume from target's durable CRCL journal; does not silently retry")
    ns = ap.parse_args()
    push(ns.host, ns.file, ns.port, ns.token, ns.chunk, not ns.verify_only, ns.resume)


if __name__ == "__main__":
    main()
