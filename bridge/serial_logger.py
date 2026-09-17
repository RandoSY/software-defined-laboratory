#!/usr/bin/env python3
"""Minimal SDL host bridge for the first acceptance path.

Reads human-readable lines from an SDL endpoint, prints them, and records
valid TEMP_C measurements to CSV with a host UTC timestamp.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import serial


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SDL USB-serial temperature logger")
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM3 or /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate (default: 115200)")
    parser.add_argument("--output", default="sdl_temperature.csv", help="CSV output path")
    parser.add_argument(
        "--seconds",
        type=float,
        default=0,
        help="Stop after this many seconds; 0 means run until Ctrl-C",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    deadline = time.monotonic() + args.seconds if args.seconds > 0 else None

    try:
        with serial.Serial(args.port, args.baud, timeout=1) as ser, output_path.open(
            "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["host_utc", "temperature_c"])
            f.flush()

            # Many Uno-class boards reset when the serial port opens.
            time.sleep(2.0)
            ser.reset_input_buffer()

            print(f"Listening on {args.port} at {args.baud} baud")
            print(f"Logging valid temperatures to {output_path}")

            while deadline is None or time.monotonic() < deadline:
                raw = ser.readline()
                if not raw:
                    continue

                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                print(line)

                fields = line.split(",")
                if len(fields) != 2 or fields[0] != "TEMP_C":
                    continue

                try:
                    temperature_c = float(fields[1])
                except ValueError:
                    print(f"Ignoring malformed temperature line: {line}", file=sys.stderr)
                    continue

                writer.writerow([utc_now(), f"{temperature_c:.3f}"])
                f.flush()

    except serial.SerialException as exc:
        print(f"Serial error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nStopped by user.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
