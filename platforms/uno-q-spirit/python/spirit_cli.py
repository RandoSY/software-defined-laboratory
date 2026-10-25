#!/usr/bin/env python3
"""UNO Q Spirit: Python control console for the on-board Arduino RouterBridge.

No network listener: control is restricted to local Unix router socket access.
Synthetic host mode is provided for pre-hardware development and CI.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Protocol

RPC_STATUS = "spirit.status"
RPC_COMMAND = "spirit.command"
FIELDS = ("timestamp_utc", "mode", "temp_state", "temp_c", "hx_state", "hx_counts", "hx_grams", "ultrasonic_state", "distance_cm", "spectral_state", "spectrum_18", "loop_ticks")

# Both the standalone CLI and dashboard use these exact RPC names. Keep them
# synchronized with Bridge.provide_safe() in UNO_Q_Spirit.ino.
class Transport(Protocol):
    def call(self, method: str, *args: Any, timeout: float = 5) -> str: ...


class LocalBridge:
    """Short-lived connection to the board-local Router Bridge socket."""
    def __init__(self) -> None:
        self.bridge = None

    def __enter__(self) -> "LocalBridge":
        try:
            from arduino.router_bridge import Bridge
        except ImportError as exc:
            raise RuntimeError("Install: python -m pip install arduino-router-bridge") from exc
        self.bridge = Bridge()
        if not self.bridge.connect(timeout=5):
            self.bridge.disconnect()
            raise ConnectionError("UNO Q router not connected within five seconds")
        return self

    def __exit__(self, *_: object) -> None:
        if self.bridge is not None:
            self.bridge.disconnect()

    def call(self, method: str, *args: Any, timeout: float = 5) -> str:
        assert self.bridge is not None
        return self.bridge.call(method, *args, timeout=timeout)


class MockBridge:
    """Synthetic host transport for CLI development; it does not emulate hardware."""
    def __init__(self) -> None:
        self.mode = "synthetic"
        self.running = True
        self.index = 0
        self.gain = 6
        self.interval = 1000
        self.profile = "all"

    def __enter__(self) -> "MockBridge": return self
    def __exit__(self, *_: object) -> None: pass

    def call(self, method: str, *args: Any, timeout: float = 5) -> str:
        if method == RPC_COMMAND:
            cmd = str(args[0]).strip()
            if cmd in ("mode synthetic", "mode live"):
                self.mode = cmd.split()[-1]
            elif cmd in ("start", "stop"):
                self.running = cmd == "start"
            elif cmd.startswith("cal grams "):
                try:
                    grams=float(cmd[10:]); assert grams>0
                except (ValueError,AssertionError):
                    return json.dumps({"ok": False, "error": "calibration_precondition"})
                if self.mode != "live": return json.dumps({"ok": False, "error": "calibration_precondition"})
            elif cmd in ("profile prototype", "profile all"):
                self.profile = cmd.split()[-1]
            elif cmd == "tare" or cmd == "reset-stats":
                pass
            elif cmd.startswith("gain "):
                try:
                    v = int(cmd[5:])
                    if v not in range(13): raise ValueError
                    self.gain = v
                except ValueError: return json.dumps({"ok": False, "error": "bad_gain"})
            elif cmd.startswith("interval "):
                try:
                    v = int(cmd[9:])
                    if not 100 <= v <= 10000: raise ValueError
                    self.interval = v
                except ValueError: return json.dumps({"ok": False, "error": "bad_interval"})
            elif cmd != "help":
                return json.dumps({"ok": False, "error": "unknown_command"})
            return json.dumps({"ok": True, "mock": True})
        if method != RPC_STATUS:
            raise KeyError(method)
        self.index += 1
        t = self.index * 0.15
        state = "SYNTH" if self.mode == "synthetic" else "MISSING"
        def sensor(val: float | None, enabled: bool = True) -> dict:
            actual_state = state if enabled or self.mode == "synthetic" else "DISABLED"
            return {"state": actual_state, "value": val if actual_state == "SYNTH" else None,
                    "ok_count": self.index if actual_state == "SYNTH" else 0, "error_count": 0}
        return json.dumps({"schema": 1, "mode": self.mode, "profile": self.profile, "run": self.running,
            "uptime_ms": int(t * 1000), "interval_ms": self.interval, "bridge_ok": True,
            "temp_c": sensor(round(22 + 2 * math.sin(t), 3) if self.mode == "synthetic" else None),
            "hx711_counts": sensor(82500 + int(100 * math.sin(t)) if self.mode == "synthetic" else None, self.profile != "prototype"),
            "hx711_grams": None, "hx711_calibrated": False,
            "distance_cm": sensor(round(50 + 10 * math.sin(t), 3) if self.mode == "synthetic" else None, self.profile != "prototype"),
            "spectral": {"state": state, "gain_code": self.gain,
                "ok_count": self.index if self.mode == "synthetic" else 0, "error_count": 0,
                "channels": [round(1200 + j * 210 + 150 * math.sin(t + j / 6)) if self.mode == "synthetic" else 0 for j in range(18)]},
            "jitter_std_ms": 0, "loop_ticks": self.index})


def decode(raw: Any) -> dict:
    if isinstance(raw, bytes): raw = raw.decode("utf-8")
    data = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(data, dict): raise ValueError("Bridge response must be a JSON object")
    return data


def request(client: Transport, command: str) -> dict:
    response = decode(client.call(RPC_COMMAND, command, timeout=5))
    if response.get("ok") is not True:
        raise ValueError(f"STM32 rejected command {command!r}: {response.get('error', response)}")
    return response


def sample(client: Transport) -> dict:
    """Fetch one schema-1 telemetry payload and reject incomplete spectra."""
    data = decode(client.call(RPC_STATUS, timeout=5))
    if data.get("schema") != 1:
        raise ValueError("Unsupported telemetry schema version")
    required = ("mode", "temp_c", "hx711_counts", "distance_cm", "spectral")
    if any(key not in data for key in required):
        raise ValueError("Incomplete telemetry sample")
    ch = data["spectral"].get("channels")
    if not isinstance(ch, list) or len(ch) != 18:
        raise ValueError("Spectral array must have 18 readout slots")
    return data


def flatten(data: dict) -> dict:
    """Convert nested Bridge JSON into one row matching the CLI CSV header."""
    return {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": data["mode"],
        "temp_state": data["temp_c"]["state"],
        "temp_c": data["temp_c"]["value"],
        "hx_state": data["hx711_counts"]["state"],
        "hx_counts": data["hx711_counts"]["value"],
        "hx_grams": data.get("hx711_grams"),
        "ultrasonic_state": data["distance_cm"]["state"],
        "distance_cm": data["distance_cm"]["value"],
        "spectral_state": data["spectral"]["state"],
        "spectrum_18": json.dumps(data["spectral"]["channels"], separators=(",", ":")),
        "loop_ticks": data.get("loop_ticks"),
    }


def execute(client: Transport, args: argparse.Namespace) -> int:
    if args.action in ("mode", "profile", "gain", "interval"):
        cmd = f"{args.action} {args.value}"
        print(json.dumps(request(client, cmd), indent=2)); return 0
    if args.action == "cal":
        print(json.dumps(request(client, f"cal grams {args.grams}"), indent=2)); return 0
    if args.action in ("start", "stop", "tare", "reset-stats"):
        print(json.dumps(request(client, args.action), indent=2)); return 0
    if args.action == "shell":
        print("UNO Q Spirit CLI; type 'status', commands shown in --help, or 'quit'")
        while True:
            try: line = input("spirit> ").strip()
            except (EOFError, KeyboardInterrupt): return 0
            if line in ("quit", "exit"): return 0
            if not line: continue
            try:
                print(json.dumps(sample(client) if line in ("status", "sample") else request(client, line), indent=2))
            except (OSError, RuntimeError, ValueError, TimeoutError, ConnectionError) as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
    if args.action == "status":
        print(json.dumps(sample(client), indent=2));return 0
    if args.action == "capture":
        # Keep one row for every requested time slot after Bridge failures; the
        # explicit ERROR mode marks gaps for downstream analysis.
        path = Path(args.output)
        if args.count < 1 or args.count > 100000: raise ValueError("count must be 1..100000")
        if not 0.1 <= args.period <= 60: raise ValueError("period must be 0.1..60 seconds")
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader()
            for i in range(args.count):
                try:
                    row = flatten(sample(client))
                except (ValueError, RuntimeError, OSError, TimeoutError, ConnectionError) as exc:
                    print(f"WARNING: lost sample {i+1}: {exc}", file=sys.stderr)
                    row = {field: None for field in FIELDS}
                    row["timestamp_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    row["mode"] = "ERROR"
                writer.writerow(row)
                if i + 1 < args.count: time.sleep(args.period)
        print(f"Wrote {args.count} telemetry rows to {path}")
        return 0
    raise ValueError(f"Unknown action: {args.action}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="UNO Q Spirit Arduino Bridge instrument console")
    ap.add_argument("--mock", action="store_true", help="local deterministic simulator; no device required")
    subs = ap.add_subparsers(dest="action", required=True)
    for name in ("status", "start", "stop", "tare", "reset-stats", "shell"):
        subs.add_parser(name)
    mode = subs.add_parser("mode"); mode.add_argument("value", choices=["synthetic", "live"])
    profile = subs.add_parser("profile"); profile.add_argument("value", choices=["prototype", "all"])
    gain = subs.add_parser("gain"); gain.add_argument("value", type=int, choices=range(13))
    interval = subs.add_parser("interval"); interval.add_argument("value", type=int)
    cal = subs.add_parser("cal"); cal.add_argument("grams", type=float)
    capture = subs.add_parser("capture"); capture.add_argument("--count", type=int, default=10)
    capture.add_argument("--period", type=float, default=1.0)
    capture.add_argument("--output", default="spirit_samples.csv")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with (MockBridge() if args.mock else LocalBridge()) as client:
            return execute(client, args)
    except (OSError, RuntimeError, ValueError, TimeoutError, ConnectionError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
