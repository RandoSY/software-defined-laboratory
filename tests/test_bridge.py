from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from protocol import parse_temperature_line
from serial_logger import log_lines


class ProtocolTests(unittest.TestCase):
    def test_valid_temperature(self) -> None:
        sample = parse_temperature_line("TEMP_C,23.625")
        self.assertIsNotNone(sample)
        self.assertAlmostEqual(sample.celsius, 23.625)

    def test_non_measurement_records_are_ignored(self) -> None:
        self.assertIsNone(parse_temperature_line("SDL,READY,DS18B20"))
        self.assertIsNone(parse_temperature_line("ERROR,SENSOR"))

    def test_malformed_temperature_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_temperature_line("TEMP_C,not-a-number")
        with self.assertRaises(ValueError):
            parse_temperature_line("TEMP_C,23.0,extra")

    def test_out_of_range_temperature_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_temperature_line("TEMP_C,126")


class LoggerTests(unittest.TestCase):
    def test_fixture_lines_become_csv(self) -> None:
        lines = [
            "SDL,READY,DS18B20\n",
            "TEMP_C,21.125\n",
            "ERROR,SENSOR\n",
            "TEMP_C,21.250\n",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample.csv"
            valid, malformed = log_lines(lines, output)
            self.assertEqual(valid, 2)
            self.assertEqual(malformed, 0)

            with output.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["temperature_c"], "21.125")
            self.assertEqual(rows[1]["temperature_c"], "21.250")


if __name__ == "__main__":
    unittest.main()
