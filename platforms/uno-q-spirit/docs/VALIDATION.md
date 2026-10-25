# Validation evidence — 2026-10-25

**Executed locally in isolated development environment, not on the user's UNO Q.**

| Check | Outcome | Evidence/limits |
|---|---|---|
| Python `unittest discover` | PASS | 14 named tests, including missing mock sensors, malformed response, invalid gain, CSV and bridge timeouts |
| C++ standard-library filter assertions | PASS | Signed 24-bit edges, echo conversion, invalid values, running moments, intervals; `g++ -std=c++17 -Wall -Wextra -Werror` |
| Arduino sketch built with **host C++ mock headers** | PASS | Sketch syntax under stubbed Arduino, Zephyr kernel and Adafruit interfaces; simulated absent sensors and mode commands |
| Synthetic host CLI | PASS | JSON sample and CSV capture in mock transport |
| Arduino UNO Q native board-core compile | PASS (2026-10-25) | Arduino CLI 1.5.1, Zephyr core 1.0.0; details in board build continuation below |
| Physical STM32 U585 upload | PASS (2026-10-25) | Authenticated `remoteocd` network upload completed with exit 0; runtime telemetry still unverified |
| Electrical safety test of original AVR Spirit PCB | NOT RUN | Original physical schematic/PCB not furnished; source PDF explicitly 5 V-only |
| Sensor accuracy / spectral fidelity | NOT RUN | Must characterize with actual sensor module, controlled lighting, standards and scope |
| End-to-end Arduino Bridge | BLOCKED (2026-10-25) | Status call attempted after upload; router socket is inaccessible to current `arduino` user (group permission). Host harness remains the only successful Bridge check. |

## Reproduction

```bash
python3 -m unittest discover -s tests -v
c++ -std=c++17 -Wall -Wextra -Werror tests/cpp/test_filters.cpp -o /tmp/spirit_filters && /tmp/spirit_filters
c++ -std=c++17 -Wall -Wextra -Werror -Itests/stubs -x c++ tests/cpp/test_sketch.cpp -o /tmp/spirit_sketch && /tmp/spirit_sketch
python3 python/spirit_cli.py --mock status
```

No hardware function is certified. This is **a software engineering preview with disciplined validation boundaries**.

**Review addendum (2026-10-25):** Verified official UNO Q default Wire D20/D21 vs historical A4/A5, added direct `profile prototype` CLI, and cleared cached temperature validity on DS18B20 probe or read failures. Physical hardware and genuine UNO Q board-core compilation remain unverified.

## Board build and install attempt — 2026-10-25

**Operator:** Codex session on the UNO Q Linux host (`arduino` account). The user authorized building and installing the code for testing and requested a clear activity record. No firmware was installed because the native compile could not pass its dependency checks.

| Step | Command / observation | Result |
|---|---|---|
| Identify board | `cat /sys/firmware/devicetree/base/compatible \| tr '\0' '\n'` | `arduino,imola`, `qcom,qrb2210`, `qcom,qcm2290`; identified as **UNO Q**. |
| Check toolchain | `arduino-cli version`, `arduino-cli core list`, `arduino-cli board listall uno` | Arduino CLI 1.5.1; `arduino:zephyr` 1.0.0 installed; FQBN confirmed as `arduino:zephyr:unoq`. |
| Check libraries | `arduino-cli lib list` | No user libraries installed. The platform includes a `Wire` library but not the application dependencies. |
| Attempt native compile | `arduino-cli compile --fqbn arduino:zephyr:unoq --build-path /tmp/uno_q_spirit_build UNO_Q_Spirit` | **FAILED** before compiling the sketch: `OneWire.h` was not found and the platform Bridge stub emitted an error requiring the real `Arduino_RouterBridge` library. `Adafruit_AS7343` and its `Adafruit BusIO` dependency are also absent. |
| Attempt library catalog access | `arduino-cli lib search 'Adafruit AS7343'` (also tried for OneWire and Arduino_RouterBridge) | **BLOCKED**: Arduino CLI could not download `library_index.tar.bz2`; DNS/network access to `downloads.arduino.cc` is denied in this environment. |
| Check board discovery | `arduino-cli board list` | **BLOCKED**: serial discovery failed with `Cannot START_SYNC: operation not permitted`; no boards were listed. No `/dev/ttyHS*`, `/dev/ttyACM*`, or `/dev/ttyUSB*` device nodes were visible to this process. |
| Check App CLI route | `arduino-app-cli version`, `config get`, `app ps --all` | CLI 0.14.0 is present, but it cannot reach its daemon at localhost:8800 and Docker status listing fails with permission denied on `/var/run/docker.sock`. App status could not be established. |
| Upload | Not attempted | There is no successful native build artifact, and no upload-capable board connection was discovered. No firmware was flashed and no running app was stopped. |

At the time of this initial attempt, the platform package showed its supported `remoteocd`/ADB uploader, but the shell could not access board discovery or the library index. Network and device discovery later became available; see the continuation below. The initial App CLI status check also failed on Docker socket permissions, but the later status check succeeded and reported no registered/running Apps.

### Initial blockers and follow-up

Network access, library installation, native compilation, and upload were resolved as documented below. App CLI container visibility and read-only Bridge telemetry remain unavailable. Keep the shield disconnected until electrical checks in `PINS_AND_SAFETY.md` are complete; the unmodified historical 5-V shield remains unsafe.

## Board build and upload continuation — 2026-10-25

After the environment gained network access, the required dependencies were installed using Arduino CLI. The resolved versions were OneWire 2.3.8, Adafruit AS7343 1.1.0, Adafruit BusIO 1.17.4, Arduino_RouterBridge 0.4.4, Arduino_RPClite 0.3.1, MsgPack 0.4.2, DebugLog 0.8.4, ArxContainer 0.7.0 and ArxTypeTraits 0.3.2.

The board was discovered as an Arduino UNO Q at `192.168.0.165` using the `network` protocol. `arduino-cli compile --fqbn arduino:zephyr:unoq --build-path /tmp/uno_q_spirit_build UNO_Q_Spirit` **PASSED** with Arduino CLI 1.5.1, Arduino Zephyr board core 1.0.0 and ARM Zephyr GCC 14.3.0. Reported image size: **132,924 bytes / 786,432 bytes flash (16%)**. Reported global RAM: **62,904 bytes / 262,144 bytes (23%)**.

Upload command: `arduino-cli upload --fqbn arduino:zephyr:unoq --port 192.168.0.165 --protocol network --build-path /tmp/uno_q_spirit_build --verify UNO_Q_Spirit`. The first invocation stopped before flashing because it looked in the default build cache instead of the custom build path. Retried with the build path; authenticated remote upload connected to the STM32U585, programmed the sketch image, and exited **0**. The upload password was provided interactively and is intentionally omitted from this record.

The Python control dependency was then installed in isolated environment `/home/arduino/.venvs/uno-q-spirit`: `arduino-router-bridge` 0.5.1 and `msgpack` 1.2.3. The stock system Python has no pip, and `python3-venv` is not installed; the venv was created with `--without-pip` and bootstrapped using `get-pip.py` from `bootstrap.pypa.io`.

Post-upload check: `/home/arduino/.venvs/uno-q-spirit/bin/python python/spirit_cli.py status` **FAILED to connect** to the local router within five seconds. The router service is active, but `/var/run/arduino-router.sock` is `root:arduino-router` mode `0660`, while this shell's `arduino` user is not a member of `arduino-router`. `arduino-app-cli monitor` connected but produced no serial output during the five-second observation; the sketch does not currently print startup messages. A later `arduino-app-cli app ps --all` succeeded and returned an empty app list, so no App container/log stream is available for this standalone sketch. No command switched the firmware to live mode; sensor wiring/electrical safety checks remain pending.

**Result at this point:** native build and remote MCU upload passed. The first Bridge RPC attempt was blocked by router socket permissions; see the permission and runtime validation update below. Do not enable live sensor mode until following `PINS_AND_SAFETY.md`.

## Router permission and hardware smoke check — 2026-10-25

With the user's authorization, the `arduino` account was added to the `arduino-router` group using `sudo usermod -aG arduino-router arduino`. This grants access to `/var/run/arduino-router.sock` (owned by `root:arduino-router`, mode `0660`). The current shell's supplementary groups were refreshed for each check using `sg arduino-router -c`; a new login will inherit the group automatically.

The live command `/home/arduino/.venvs/uno-q-spirit/bin/python python/spirit_cli.py status` **PASSED** through the local router. Observed telemetry: schema 1, `mode=synthetic`, `run=true`, `bridge_ok=true`, all four sensor states `SYNTH`, and zero sensor errors. `ok_count` advanced to 228, confirming the firmware was running and serving changing synthetic telemetry after upload.

End-to-end CSV smoke check **PASSED** with three samples at one-second intervals:

```bash
sg arduino-router -c '/home/arduino/.venvs/uno-q-spirit/bin/python /home/arduino/UNO_Q_Spirit_v0.1.1_reviewed/python/spirit_cli.py capture --count 3 --period 1 --output /tmp/uno_q_spirit_hardware_smoke.csv'
```

The output file is `/tmp/uno_q_spirit_hardware_smoke.csv`; it contains three changing synthetic samples, valid CSV headers, 18 spectral slots per row, and increasing `loop_ticks`. No live mode or sensor access was attempted. Physical sensor behavior, real Bridge commands beyond status/capture, and electrical safety remain unverified.

## Interactive Python CLI check — 2026-10-25

Ran the actual interactive shell over the UNO Q's local Router Bridge as a process with `arduino-router` group access:

```text
$ sg arduino-router -c '/home/arduino/.venvs/uno-q-spirit/bin/python /home/arduino/UNO_Q_Spirit_v0.1.1_reviewed/python/spirit_cli.py shell'
UNO Q Spirit CLI; type 'status', commands shown in --help, or 'quit'
spirit> status
{
  "schema": 1,
  "mode": "synthetic",
  "run": true,
  "profile": "all",
  "bridge_ok": true,
  "temp_c": {"state": "SYNTH", "value": 19.64, "ok_count": 304, "error_count": 0},
  "hx711_counts": {"state": "SYNTH", "value": 81849.0, "ok_count": 304, "error_count": 0},
  "distance_cm": {"state": "SYNTH", "value": 56.944, "ok_count": 304, "error_count": 0},
  "spectral": {"state": "SYNTH", "gain_code": 6, "ok_count": 304, "error_count": 0, "channels": [18 values]},
  "loop_ticks": 138506
}
spirit> help
{"ok": true, "commands": ["mode synthetic", "mode live", "profile prototype", "profile all", "start", "stop", "tare", "gain 0..12", "interval 100..10000", "reset-stats", "cal grams <known mass>"]}
spirit> quit
```

Both `status` and `help` returned successfully. The shell was closed with `quit`; no acquisition mode/profile was changed.

## Three-second synthetic temperature CSV — 2026-10-25

The user requested a DS18B20 temperature log and specified **synthetic temperature data**, so live mode was not enabled and no sensor was accessed. A pre-capture `status` response confirmed `mode=synthetic`, `run=true`, and `temp_c.state=SYNTH`.

CLI interaction:

```text
$ sg arduino-router -c '/home/arduino/.venvs/uno-q-spirit/bin/python /home/arduino/UNO_Q_Spirit_v0.1.1_reviewed/python/spirit_cli.py capture --count 10 --period 3 --output /home/arduino/UNO_Q_Spirit_v0.1.1_reviewed/captures/uno_q_spirit_synthetic_telemetry_3s.csv'
Wrote 10 telemetry rows to /home/arduino/UNO_Q_Spirit_v0.1.1_reviewed/captures/uno_q_spirit_synthetic_telemetry_3s.csv
```

The CLI raw capture contains all telemetry fields. A temperature-only review file was derived from those same rows at `captures/uno_q_spirit_synthetic_temperature_3s.csv`, with columns `sample,timestamp_utc,mode,temperature_state,temperature_c`. CSV validation confirmed 10 rows, every row in `synthetic` mode with `SYNTH` temperature state and a value, and nine timestamp gaps of exactly 3 seconds (UTC timestamps are rounded to whole seconds). The recorded temperatures vary from 19.505°C to 22.419°C; they are simulated values, not DS18B20 measurements.

## LAN experiment dashboard — 2026-10-25

Implemented `python/dashboard_server.py` and the branded `dashboard/` web interface. It polls `spirit.status` on the Linux MPU, shows live sensor state and a temperature trend, lets the user start/stop Linux-side experiment recording, stores run metadata and telemetry snapshots in SQLite, and downloads per-run CSV. The project SVG logo and matching favicon/colors are served locally. The interface marks synthetic data and does not expose a control that switches the MCU into live mode. CSV contains UTC sample time, all sensor states/values, calibration status, spectral gain and 18 raw slots, and loop ticks.

An isolated smoke server on port 7001 with its database under `/tmp/uno-q-spirit-dashboard-smoke` passed health, HTML, CSS/JS/logo delivery, Bridge status, experiment start/stop, SQLite persistence and CSV download checks; the temporary run held three synthetic rows. The active server was then started on `0.0.0.0:7000` with Bridge group access. From the board's network address `192.168.0.165`, `/`, `/style.css`, `/app.js`, `/brand/uno-q-spirit-logo.svg` all returned HTTP 200 and `/healthz` returned `{"ok":true,"bridge_ok":true}`. A Chrome client at `192.168.0.218` subsequently requested the page, assets, `/api/state`, and `/api/runs` successfully. Runtime details and startup instructions are in `docs/DASHBOARD.md`.

The dashboard uses plain HTTP without authentication and is intended for the trusted local network. It currently runs in the active shell session; reboot/session-loss startup management has not been configured. Visual browser rendering was not inspected by an automated screenshot tool, though the browser loaded and executed the app endpoints.

**Visual refinement:** Switched dashboard surfaces to navy/slate with higher-contrast cyan, teal, lavender, mint and warm pastel sensor accents while retaining the project logo. Verified the updated HTML and stylesheet return HTTP 200 at `192.168.0.165:7000`.

**Tabbed organization and control feedback:** Added accessible Monitor, Experiments, and Archive tabs with active-run indicators, operator messages, run progress, save confirmation, and CSV access. A Chromium-driven interaction check against an isolated temporary database verified tab switching, start feedback/badge, stop/save feedback, archive listing, and CSV download with the HX711 calibration column. The temporary test data is under `/tmp/uno-q-spirit-dashboard-ui-test`, not the permanent experiment archive. The active dashboard remains available on port 7000.
