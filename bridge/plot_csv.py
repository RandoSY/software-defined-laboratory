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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.csv_path)

    times: list[datetime] = []
    temperatures: list[float] = []

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(datetime.fromisoformat(row["host_utc"]))
            temperatures.append(float(row["temperature_c"]))

    if not times:
        raise SystemExit("No temperature rows found in CSV file.")

    plt.figure()
    plt.plot(times, temperatures)
    plt.xlabel("Host time (UTC)")
    plt.ylabel("Temperature (°C)")
    plt.title("SDL DS18B20 Temperature")
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    plt.show()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
