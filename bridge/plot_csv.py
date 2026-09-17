#!/usr/bin/env python3
"""Plot CSV output produced by serial_logger.py."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot SDL temperature CSV data")
    parser.add_argument("csv_path", help="CSV file produced by serial_logger.py")
    parser.add_argument(
        "--output",
        help="Save a PNG instead of opening an interactive plot window",
    )
    return parser.parse_args()


def load_csv(path: Path) -> tuple[list[datetime], list[float]]:
    times: list[datetime] = []
    temperatures: list[float] = []

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected = {"host_utc", "temperature_c"}
        if not expected.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV must contain columns: {sorted(expected)}")

        for row in reader:
            times.append(datetime.fromisoformat(row["host_utc"]))
            temperatures.append(float(row["temperature_c"]))

    if not times:
        raise ValueError("No temperature rows found in CSV file.")

    return times, temperatures


def main() -> int:
    args = parse_args()
    times, temperatures = load_csv(Path(args.csv_path))

    plt.figure()
    plt.plot(times, temperatures)
    plt.xlabel("Host time (UTC)")
    plt.ylabel("Temperature (°C)")
    plt.title("SDL DS18B20 Temperature")
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output)
        print(f"Saved {output}")
    else:
        plt.show()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
