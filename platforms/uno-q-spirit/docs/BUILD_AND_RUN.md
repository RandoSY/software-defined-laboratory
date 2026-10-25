# Install, run and command the UNO Q Spirit firmware

**First hardware attempt?** Follow the [two-sensor prototype-shield quickstart](PROTOTYPE_SHIELD_QUICKSTART.md) and use `profile prototype` **before** `mode live`.

The sketch uses UNO Q `Wire` on **D20/D21**; historical Spirit A4/A5 is **not** the default `Wire` bus.

## 1. Build on Arduino IDE

- In Arduino IDE 2.x install/update **Arduino UNO Q Boards**. Select **Arduino UNO Q** (MCU sketch target).
- Libraries: **Adafruit AS7343**, **Adafruit BusIO**, **OneWire**, **Arduino_RouterBridge**; `Wire` comes from the board core.
- Open `UNO_Q_Spirit/UNO_Q_Spirit.ino` in Arduino IDE and click **Verify**; note Arduino IDE and core versions. Fix API incompatibilities before connecting the sensor shield.
- Upload through the UNO Q's documented workflow. Do not `west flash` a standalone Zephyr firmware over the Arduino sketch loader.
- The Bridge library requires the Arduino Router on Debian; the firmware itself launches Bridge registration in a **separate Zephyr thread** so sensor acquisition can run if initialization blocks on an absent Linux router.

If `arduino-cli` is available on IAS-Q, confirm the core with:

```bash
arduino-cli core list
arduino-cli board listall uno
arduino-cli lib list
arduino-cli compile --fqbn arduino:zephyr:unoq UNO_Q_Spirit
```

`arduino:zephyr:unoq` is a probable package FQBN; **confirm with `board listall`** because actual toolchain package naming is version-dependent. For upload use the documented Arduino UNO Q core upload facility and do not invent a serial flash port.

## 2. Python on Debian

```bash
python3 -m venv ~/uno-q-spirit-venv
. ~/uno-q-spirit-venv/bin/activate
pip install arduino-router-bridge
python python/spirit_cli.py status
python python/spirit_cli.py shell
```

CLI interactive examples:

```text
spirit> status
spirit> mode synthetic
spirit> gain 6
spirit> interval 1000
spirit> stop
spirit> start
spirit> profile prototype
spirit> mode live
spirit> tare
spirit> cal grams 100
spirit> quit
```

Only use `mode live` after reading `PINS_AND_SAFETY.md` and performing the unpowered and powered electrical checks. The gain code follows AS7343's library enum (0=0.5x,1=1x,...6=64x,...12=2048x); high gain improves low-light counts at the cost of possible saturation. For best fidelity choose low enough gain and short enough integration to prevent saturation, then repeat measurements under controlled lighting to estimate variance. Integration-time adjustment from the CLI is a future feature; startup is approximately 50 ms per auto-SMUX cycle with ATIME 29 and ASTEP 599 as in Adafruit's example.

## 3. Local development without the board

```bash
python3 python/spirit_cli.py --mock status
python3 python/spirit_cli.py --mock capture --count 15 --period 0.1 --output measurements.csv
python3 -m unittest discover -s tests -v
c++ -std=c++17 -Wall -Wextra -Werror tests/cpp/test_filters.cpp -o /tmp/spirit_filters && /tmp/spirit_filters
c++ -std=c++17 -Wall -Wextra -Werror -Itests/stubs -x c++ tests/cpp/test_sketch.cpp -o /tmp/spirit_sketch && /tmp/spirit_sketch
```

Mock mode has no hardware access and deliberately does not pretend to exercise MCU peripherals.

## 4. Returned telemetry

`spirit.status` returns a JSON string with schema 1. Keys: `mode`, `run`, `uptime_ms`, `temp_c`, `hx711_counts`, `hx711_grams`, `hx711_calibrated`, `distance_cm`, `spectral`, `jitter_std_ms`, `hx_counts_stddev`, `ultrasonic_cm_stddev`, `loop_ticks`. Each major sensor includes `state`, `value` (null unless OK/SYNTH), `ok_count`, `error_count`. `spectral.channels` has 18 integer positions; the `state` reports saturation. The `interval` command changes synthetic output interval, **not** the hardware acquisition periods.

`spirit.command` takes one string and returns a JSON string with `ok` true/false and optional error. `tare` adjusts a RAM offset, while `cal grams <positive mass>` computes counts/gram from a known mass in live mode only after tare and good HX711 samples. Do not assume a negative scale is an error; it can reflect gauge polarity.

## 5. Debugging

The UNO Q exposes internal STM32 SWD via Qualcomm and has an `arduino-debug` / OpenOCD workflow. Debug symbols for dynamically relocated Arduino sketches require correct runtime symbol addresses. A host C++ syntax check does **not** prove that interrupt locking, bus timeouts or Zephyr scheduling work on silicon. Inspect logic analyzer captures before declaring HX711 or OneWire timing stable. Official: https://docs.zephyrproject.org/latest/boards/arduino/uno_q/doc/index.html

## 6. Chrome experiment dashboard

Start the Linux-side dashboard from the project directory:

```bash
source /home/arduino/.venvs/uno-q-spirit/bin/activate
python python/dashboard_server.py
```

Open **http://192.168.0.165:7000** in Chrome on the same LAN. The dashboard polls the MCU's `spirit.status` RPC, displays the reported sensor states, records experiment snapshots on Linux, stores runs in SQLite, and provides per-run CSV downloads. Starting/stopping a dashboard run controls Linux recording only; it does not switch the firmware between synthetic and live modes. Full details, storage path and API endpoints are in [`DASHBOARD.md`](DASHBOARD.md).
