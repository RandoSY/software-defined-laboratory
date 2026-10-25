![UNO Q Spirit engineering concept logo](assets/uno-q-spirit-logo.svg)

# UNO Q Spirit · Instrumentation Verification Suite

**Release:** `0.1.1-prototype` — engineering preview, 25 October 2026  
**Target:** Arduino UNO Q STM32U585 running Arduino's Zephyr-based Arduino core.  
**Control plane:** Qualcomm Debian 13 + local Arduino RouterBridge, Python CLI.  
**Provenance:** Adapted from the user's **Nugget 2-Wire Sensor Shield — KiCad Autorouting and Programmer's Guide**, v0.2x, pages 2, 4–6, plus the AVR Spirit UNO Q conversion prompt.  
**Hardware status:** **UNVERIFIED; DO NOT CONNECT AN UNMODIFIED 5-V SHIELD.**

## Purpose

Exercise the original AVR Spirit 2-Wire shield's sensor interfaces safely on a 3.3 V UNO Q, with missing-sensor fault isolation, deterministic mock data, instrument-quality statistics, tunable AS7343 gain, explicit HX711 tare/calibration, and a local CLI/CSV recording interface. The STM32 runs the Arduino sketch. Zephyr schedules a separate Bridge initialization thread, keeping local acquisition alive if Linux routing is unavailable during startup.

## Source map

- `assets/uno-q-spirit-logo.svg` — scalable logo for GitHub and documentation; `assets/uno-q-spirit-logo.png` — original generated concept image (included in ZIP but omitted from GitHub text release).

- `UNO_Q_Spirit/UNO_Q_Spirit.ino` — complete Arduino C++ sketch, runtime RPC endpoints `spirit.status` / `spirit.command`.
- `UNO_Q_Spirit/filters.h` — pure C++ algorithms and numeric guards.
- `python/spirit_cli.py` — Debian CLI, local mock mode and CSV export.
- `python/dashboard_server.py` + `dashboard/` — LAN experiment dashboard, SQLite run archive and per-run CSV export; setup in [`docs/DASHBOARD.md`](docs/DASHBOARD.md).
- `tests/test_spirit_cli.py`, `tests/cpp/` and `tests/stubs/` — desktop tests and mock Arduino/Zephyr compile harness.
- `docs/PRODUCT_SPEC.md` — requirements, assumptions, acceptance and limitations.
- `docs/PINS_AND_SAFETY.md` — historical documented pin contract, 3.3 V adaptation plan.
- `docs/BUILD_AND_RUN.md` — Arduino setup, commands, Zephyr specifics, host CLI.
- **`docs/PROTOTYPE_SHIELD_QUICKSTART.md` — start here: two sensors on an empty prototype shield (no Spirit PCB needed).**
- **[Spectral sensor selection and fidelity](docs/SPECTRAL_SELECTION.md)** — AS7343 first target; compare with newer TCS3448 before sensor procurement.
- **[Standalone AS7343 Qwiic test](examples/as7343-qwiic-test/README.md)** — test the spectrometer directly on UNO Q without Spirit shield hardware.
- `docs/TEST_PLAN.md` — electrical and functional acceptance protocol.
- `docs/VALIDATION.md` — evidence of tests actually run.

## Historical pin contract

| Function | Arduino UNO Q header | Original signal |
|---|---|---|
| DS18B20 1-Wire | D2 | D2_ONEWIRE |
| HX711 DOUT | D3 | HX711_DT |
| HX711 PD_SCK | D4 | HX711_SCK |
| START input, active-low | D5 | D5_START |
| TARE input, active-low | D6 | D6_TARE |
| HC-SR04 TRIG | D7 | D7_TRIG |
| HC-SR04 ECHO | D8 | D8_ECHO |
| **Active buzzer module** signal | D9 | D9_BUZZER |
| I²C SDA / SCL (historical Spirit PCB) | A4 / A5 | SDA / SCL |
| **I²C SDA / SCL (current test firmware using `Wire`)** | **D20 / D21** | **UNO Q default `Wire`; AS7343 prototype** |

**Important:** The original 5-V shield had I²C on A4/A5; the UNO Q Arduino sketch uses `Wire` on **D20/D21**, so the prototype spectral sensor must be wired to **D20/D21**. ArduinoCore-zephyr provides additional buses but requires deliberate source configuration. See the [two-sensor quickstart](docs/PROTOTYPE_SHIELD_QUICKSTART.md).

The original signals are **logical mappings from the historical PDF**, not a claim that the 5-V original physical board has been converted. **The original PDF explicitly states HC-SR04 ECHO is unshifted 5 V; it is unsafe to mate the original board directly until adapted.**

## First run (no hardware)

```bash
python3 python/spirit_cli.py --mock status
python3 python/spirit_cli.py --mock capture --count 10 --period 0.1 --output samples.csv
python3 -m unittest discover -s tests -v
c++ -std=c++17 -Wall -Wextra -Werror tests/cpp/test_filters.cpp -o /tmp/spirit_filters && /tmp/spirit_filters
c++ -std=c++17 -Wall -Wextra -Werror -Itests/stubs -x c++ tests/cpp/test_sketch.cpp -o /tmp/spirit_sketch && /tmp/spirit_sketch
```

## Build for STM32

1. Install **Arduino UNO Q board** support in Arduino IDE and use the latest official core.
2. Install **Adafruit AS7343**, **Adafruit BusIO** (dependency), **OneWire**, and **Arduino_RouterBridge** libraries via Arduino Library Manager/board platform. `Wire` is provided by the core.
3. Open `UNO_Q_Spirit/UNO_Q_Spirit.ino` and select **Arduino UNO Q**, then Verify. Upload by the supported Arduino UNO Q workflow.
4. This preview has **not** been compiled with the actual UNO Q toolchain. Do not treat host-only tests as a hardware-build pass. See `docs/BUILD_AND_RUN.md`.
5. The firmware boots in **SYNTHETIC** mode. Only enter `mode live` after the shield's 3.3 V electrical qualification.

## Python control on the Qualcomm

```bash
python3 -m venv ~/spirit-venv
. ~/spirit-venv/bin/activate
pip install arduino-router-bridge
python python/spirit_cli.py status
python python/spirit_cli.py shell
python python/spirit_cli.py capture --count 100 --period 1 --output measurements.csv
```

CLI direct command or shell examples: `profile prototype` (DS18B20 + AS7343 only), `profile all`, `mode synthetic`, `mode live`, `gain 6` (64x), `interval 1000`, `tare`, `cal grams 100`, `start`, `stop`, `reset-stats` (where `cal grams` is available in the interactive shell). The host CLI never needs elevated privileges but does need permission to access the local router socket.

### Chrome experiment dashboard

On the UNO Q, run `python python/dashboard_server.py` from the project directory after activating `/home/arduino/.venvs/uno-q-spirit`. Then open **http://192.168.0.165:7000** on the same network. The dashboard records experiments on the Linux side and exports per-run CSV files. See [`docs/DASHBOARD.md`](docs/DASHBOARD.md).

## Original vs proposed changes

**Preserved:** pin assignment, educational sensor combinations, user-facing Start/Tare, active buzzer interface, 2-wire/I²C expansion.  
**Changed conceptually:** 3.3 V voltage domain, mandatory echo level shifting or proven 3.3 V ultrasonic hardware, HX711 supply audit, external power isolation, spectral AS7343 0x39 breakout, bridge telemetry, and testing strategy.  
**Not delivered:** updated KiCad schematic/PCB, manufacturing files, fabricated shield, verified electrical pin-to-net mapping on the latest original board, installed firmware on IAS-Q.

Original Arduino, Adafruit and Zephyr marks are used only to name compatible platforms and parts; this project is not affiliated with their vendors.
