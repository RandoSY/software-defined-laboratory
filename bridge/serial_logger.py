#!/usr/bin/env python3
"""Minimal SDL host bridge for the first acceptance path.

Reads human-readable SDL records from either a serial port or a text fixture,
prints them, and records valid TEMP_C measurements to CSV with a host UTC
timestamp. Fixture mode gives the repository a hardware-independent software
acceptance path.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from protocol import parse_temperature_line


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SDL temperature logger")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--port", help="Serial port, e.g. COM3 or /dev/ttyACM0")
    source.add_argument(
        "--input-file",
        help="Read endpoint-style records from a text file instead of hardware",
    )
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    parser.add_argument("--output", default="sdl_temperature.csv", help="CSV output path")
    parser.add_argument(
        "--seconds",
        type=float,
        default=0,
        help="Serial mode only: stop after this many seconds; 0 means Ctrl-C",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def log_lines(lines: Iterable[str], output_path: Path) -> tuple[int, int]:
    """Log valid temperature records.

    Returns (valid_measurement_count, malformed_measurement_count).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid = 0
    malformed = 0

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["host_utc", "temperature_c"])

        for line in lines:
            line = line.strip()
            if not line:
                continue
            print(line)

            try:
                sample = parse_temperature_line(line)
            except ValueError as exc:
                malformed += 1
                print(f"Ignoring malformed measurement: {exc}", file=sys.stderr)
                continue

            if sample is None:
                continue

            writer.writerow([utc_now(), f"{sample.celsius:.3f}"])
            f.flush()
            valid += 1

    return valid, malformed


def file_lines(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8") as f:
        yield from f


def serial_lines(port: str, baud: int, seconds: float) -> Iterable[str]:
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError(
            "pyserial is required for --port mode; install bridge/requirements.txt"
        ) from exc

    deadline = time.monotonic() + seconds if seconds > 0 else None

    try:
        with serial.Serial(port, baud, timeout=1) as ser:
            # Uno-class boards commonly reset when the port opens.
            time.sleep(2.0)
            print(f"Listening on {port} at {baud} baud", file=sys.stderr)

            while deadline is None or time.monotonic() < deadline:
                raw = ser.readline()
                if not raw:
                    continue
                yield raw.decode("utf-8", errors="replace")
    except serial.SerialException as exc:
        raise RuntimeError(f"serial error: {exc}") from exc


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    try:
        if args.input_file:
            lines = file_lines(Path(args.input_file))
        else:
            lines = serial_lines(args.port, args.baud, args.seconds)

        valid, malformed = log_lines(lines, output_path)
    except (OSError, RuntimeError) as exc:
        print(exc, file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nStopped by user.", file=sys.stderr)
        return 130

    print(
        f"Recorded {valid} temperature samples to {output_path}"
        + (f"; ignored {malformed} malformed measurement(s)" if malformed else ""),
        file=sys.stderr,
    )
    return 0 if valid > 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
