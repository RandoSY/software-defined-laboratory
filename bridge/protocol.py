"""Protocol helpers for the SDL first acceptance path."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemperatureSample:
    celsius: float


def parse_temperature_line(line: str) -> TemperatureSample | None:
    """Parse TEMP_C,<value>; return None for non-measurement lines.

    Raises ValueError for a TEMP_C line whose numeric value is malformed
    or outside the physical DS18B20 operating range.
    """
    text = line.strip()
    if not text:
        return None

    fields = text.split(",")
    if fields[0] != "TEMP_C":
        return None
    if len(fields) != 2:
        raise ValueError(f"malformed TEMP_C record: {text!r}")

    try:
        value = float(fields[1])
    except ValueError as exc:
        raise ValueError(f"non-numeric TEMP_C value: {text!r}") from exc

    if not -55.0 <= value <= 125.0:
        raise ValueError(f"TEMP_C outside DS18B20 range: {value}")

    return TemperatureSample(value)
