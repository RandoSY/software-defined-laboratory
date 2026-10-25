# UNO Q Spirit code review guide

This guide is a map for reading the prototype. The comments in the source focus on hardware assumptions, data contracts, units, and failure behavior; use this page to follow a sample end to end.

## Data path

```text
Sensors / synthetic generator
        │
        ▼
UNO_Q_Spirit/UNO_Q_Spirit.ino  (STM32 sampling + state + RPC)
        │  spirit.status / spirit.command over Router Bridge
        ├──────────────────────────────┐
        ▼                              ▼
python/spirit_cli.py          python/dashboard_server.py
        │                              ├── latest status → browser API
        └── console/CSV                 └── experiment snapshots → SQLite → CSV
```

The `examples/as7343-qwiic-test/` sketch is intentionally separate: it connects only an AS7343 breakout, trying `Wire1` Qwiic first and then `Wire` on D20/D21 and reports through Serial. It does not use the Spirit shield, Router Bridge, or any other sensor.

## Files to read in order

1. [`UNO_Q_Spirit/UNO_Q_Spirit.ino`](../UNO_Q_Spirit/UNO_Q_Spirit.ino): pin constants, acquisition state, startup mode, device cadence, RPC JSON, command validation, Bridge thread, and the main loop.
2. [`UNO_Q_Spirit/filters.h`](../UNO_Q_Spirit/filters.h): pure conversions and numeric guards shared by the sketch. HX711 values are raw counts until a RAM-only calibration exists; ultrasonic output is centimeters; temperature is Celsius.
3. [`python/spirit_cli.py`](../python/spirit_cli.py): the local Bridge transport and mock transport implement one protocol. `sample()` validates schema 1 and 18 spectral slots. `flatten()` defines the command-line CSV shape.
4. [`python/dashboard_server.py`](../python/dashboard_server.py): a one-second Bridge poll feeds the live UI; the operator-selected interval controls SQLite experiment recording separately. Stopping a run does not stop MCU acquisition.
5. [`dashboard/app.js`](../dashboard/app.js) and [`dashboard/index.html`](../dashboard/index.html): presentation, chart, accessible tabs, recording feedback, archive download, and browser-local text-size preference. The HTTP API does not expose MCU mode changes.
6. [`examples/as7343-qwiic-test/as7343-qwiic-test.ino`](../examples/as7343-qwiic-test/as7343-qwiic-test.ino): isolated `Wire1` example for sensor-only optical bring-up.

## Contracts and review cautions

- Bridge names are exactly `spirit.status` and `spirit.command`; both Python tools depend on those names and the corresponding JSON fields.
- The Spirit sketch's `profile prototype` means DS18B20 + AS7343; it only disables HX711 and ultrasonic polling. For AS7343 alone on Qwiic, use the separate example.
- The board header's default `Wire` uses D20/D21. The Qwiic connector is the separate 3.3 V `Wire1` bus. The production Spirit sketch currently initializes only `Wire`.
- `synthetic` values are simulated and should stay visibly labeled as such. The AS7343's 18 slots are raw driver readouts, not 18 calibrated wavelength bins.
- The dashboard records Linux-side snapshots; it does not provide hard real-time timing or calibration. SQLite timestamps are UTC, while MCU counters and the standalone Qwiic sketch's elapsed time are milliseconds.
- `tests/stubs/` exists to compile exercise firmware contracts on a host. Passing stub-based checks cannot prove actual board timing, I²C fault recovery, sensor accuracy, or electrical safety.

## Test and evidence map

- [`tests/test_spirit_cli.py`](../tests/test_spirit_cli.py): mock telemetry schema, parser commands, errors, and CLI CSV rows.
- [`tests/cpp/test_filters.cpp`](../tests/cpp/test_filters.cpp): conversion bounds, signed 24-bit decoding, sample statistics, and interval limits.
- [`tests/cpp/test_sketch.cpp`](../tests/cpp/test_sketch.cpp): host simulation of synthetic startup, missing sensors, profiles, and RPC command behavior.
- [`docs/TEST_PLAN.md`](TEST_PLAN.md): planned bench checks for real sensors and the standalone Qwiic path.
- [`docs/VALIDATION.md`](VALIDATION.md): recorded outcomes, including what has and has not been verified on physical hardware.
