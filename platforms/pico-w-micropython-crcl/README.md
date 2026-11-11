# Pico W SDL/CRCL — Remotely Programmable MicroPython Laboratory Node

**Version:** 1.1.0 (recovered 2026-09-21 release)  
**Hardware:** Raspberry Pi Pico W (RP2040), with optional PicoBricks  
**Status:** **desktop regression validated; actual Pico W/PicoBricks acceptance still pending**  
**Origin:** original v1.1 source archive recovered from the author's ChatGPT Library and placed in `software-defined-laboratory/platforms/pico-w-micropython-crcl/` on 2026-11-10. The code below was not rewritten as a new implementation.

## Why this project exists

In the **Software-Defined Laboratory (SDL)**, a node is a reusable instrument rather than a single-purpose firmware sketch. An operator or AI coding agent can discover sensors, run experiments, retrieve measurements, and replace *experiment-specific MicroPython code* over a network without repeatedly reflashing the Pico W. The more permanent resident runtime maintains the communications, device registry, and recovery mechanism.

```text
Codex / operator / Python client / future web dashboard
                     |
             Windows or Linux host
                     |
       +-------------+--------------------+
       |             |                    |
    USB serial   Wi-Fi / TCP :8765     BLE Nordic UART
    (recovery)   (primary host link)    (optional, disabled)
       |             |                    |
       +-------------+--------------------+
                     |
          SDL ASCII command dispatcher
                     |
     +---------------+----------------+
     |               |                |
  device roles   capabilities     CRCL updater
  and drivers    and registry    stage/verify/
                              install/health/rollback
                     |
              apps/crcl_app.py
            replaceable experiment
```

**Important distinctions:** The Pico W firmware implements **a TCP command server, not a hosted browser IDE or HTML dashboard**. A browser UI, if desired, needs a separate host-side dashboard or gateway speaking to the node. BLE support is present in source but **disabled by default and not physically validated**. The original non-wireless Raspberry Pi Pico can use USB MicroPython but lacks the Pico W's built-in Wi-Fi/BLE hardware.

## What's in this folder

| Path | Use |
|---|---|
| `board_files/` | Exact directories and scripts to copy to the Pico W filesystem root (`main.py`, `sdl/`, `drivers/`, `apps/`, `capabilities/`, `staging/`) |
| `tools/` | Host-side TCP client, acceptance checker, `crcl_push.py` updater, and interactive config creation |
| `examples/crcl_app_measure.py` | Demo dynamically replaceable measurement app |
| `tests/` | CPython regression tests for protocol, transfer, interrupted updates, sensors, and capability registration |
| `docs/` | Detailed architecture, install, command protocol, acceptance checklist and PicoBricks guide |
| `config.picobricks.example.json` | Placeholder-only configuration template, **not** live Wi-Fi credentials |
| `config.sensor_rig.example.json` | Optional external sensor setup |
| `RELEASE_VALIDATION.md` | What was tested in the v1.1 software release and what was not |
| `CHANGELOG.md`, `VERSION.txt`, `MANIFEST.sha256` | Historical release record; note manifest hashes are for the **original release**, before this improved README |

**Do not copy the entire repository folder to the Pico.** Use the *contents* of `board_files/` plus a private `/config.json` file. Root-level `sdl/`, `drivers/`, and similar folders mirror the board copies for tests and source inspection.

## First use — Windows and Pico W over USB

**Before starting:** a Pico W board, a data-capable USB cable, Python 3 on Windows, and the correct [MicroPython Pico W UF2 firmware](https://micropython.org/download/RPI_PICO_W/). The board must run MicroPython rather than CircuitPython/Arduino for these scripts. Do not overwrite an existing board without retrieving any code or data that matters to you.

1. Hold **BOOTSEL** while plugging in the Pico W and copy the Pico W MicroPython `.uf2` to the `RPI-RP2` drive. It reboots into MicroPython.
2. In PowerShell, install the official MicroPython utility:

   ```powershell
   py -m pip install --upgrade mpremote
   py -m mpremote connect list
   ```

3. Open PowerShell in **this folder**. Substitute your actual COM port (for example, `COM28`) for `COMx`. A COM port belongs to the device and may change across connections.

   ```powershell
   $PICO = "COM28"   # EXAMPLE ONLY: use the port reported by mpremote
   py -m mpremote connect $PICO exec "import os; print(os.uname())"
   ```

4. From this folder, copy each required directory *from `board_files/`* to the device's filesystem root (the `:` denotes the Pico's MicroPython filesystem):

   ```powershell
   py -m mpremote connect $PICO fs cp board_files/boot.py :boot.py
   py -m mpremote connect $PICO fs cp board_files/main.py :main.py
   py -m mpremote connect $PICO fs cp board_files/config_default.py :config_default.py
   py -m mpremote connect $PICO fs cp -r board_files/sdl :
   py -m mpremote connect $PICO fs cp -r board_files/drivers :
   py -m mpremote connect $PICO fs cp -r board_files/capabilities :
   py -m mpremote connect $PICO fs cp -r board_files/apps :
   py -m mpremote connect $PICO fs cp -r board_files/staging :
   ```

   Check `docs/INSTALL_MPREMOTE.md` for the original installation procedure. Different `mpremote` releases can vary in filesystem copy behavior; inspect `mpremote fs cp --help` if necessary. Only proceed when all expected files are present.

5. Create a local configuration without adding credentials to Git:

   ```powershell
   py tools/make_config.py --profile picobricks
   py -m mpremote connect $PICO fs cp config.json :config.json
   py -m mpremote connect $PICO reset
   ```

   The script requests Wi-Fi SSID/password and optional TCP token. **Never commit or post `config.json`.** If using a bare Pico W without PicoBricks, set `devices.enable_picobricks` to `false` in your local config before copying, and choose a compatible sensor profile.

6. Open USB terminal with `py -m mpremote connect $PICO repl` if the program and REPL are available; otherwise use a serial terminal. The v1.1 resident core should announce `Pico W SDL/CRCL Reference Node v1.1.0` and `READY`. Close any other application owning that COM port (e.g. Thonny) first.

7. Probe with these **human USB-console commands**:

   ```text
   HELP
   PING
   INFO
   DEV LIST
   I2C SCAN
   CAP LIST
   APP STATUS
   CRCL STATUS
   ```

   With PicoBricks present, test `DEV READ pb.pot`, `DEV READ pb.ldr` and `DEV WRITE pb.led 1` then `DEV WRITE pb.led 0`. An environmental sensor appears only if detected.

## Wi-Fi/TCP proof (after USB works)

The node joins your existing Wi-Fi as a station, retains the internet connection on your host, and prints its DHCP address. Substitute the actual Pico address, **not** the example IP below. The host and node must have network reachability; isolate the TCP service from the public internet.

```powershell
$IP = "192.168.1.42"  # EXAMPLE ONLY
py tools/acceptance.py $IP
```

If you set a token in `config.json`, pass the same token through `--token` to the host tool; it is **not encrypted on the wire**. The server uses port `8765` by default and SDL ASCII requests such as `CMD 101 PING`. See `docs/ARCHITECTURE.md` and `docs/CRCL_PROTOCOL.md` for details.

## Dynamic experiment deployment over Wi-Fi

Your first remote program change updates the **managed experiment application**, not the resident MicroPython firmware:

```powershell
py tools/crcl_push.py $IP examples/crcl_app_measure.py
```

The uploader stages chunks, verifies byte count and CRC32 (plus SHA-256 supplied by the host), checks Python syntax, installs the candidate, and invokes the app health check. A backup supports rollback of failed activation.

After an interrupted/uncertain transfer, **do not blindly resend the entire operation**:

```powershell
py tools/crcl_push.py $IP examples/crcl_app_measure.py --resume
```

If necessary, roll back the managed app through the SDL protocol/USB console:

```text
CMD 900 CRCL.ROLLBACK
```

The deployed application follows this contract:

```python
def health(ctx):
    return True

def setup(ctx):
    pass

def tick(ctx):
    # Nonblocking, bounded work; the resident loop needs time to serve clients.
    pass

def stop(ctx):
    pass
```

The context exposes `ctx.devices`, `ctx.lab`, `ctx.capabilities`, `ctx.emit(...)` and `ctx.now_ms()`. **Do not place infinite loops or long blocking calls in `tick()`: a program with interpreter access can still hang the node.** Only a single managed app file is dynamically transferred in v1.1; complete multi-file capability-package installation is not implemented.

## BLE, browser UI, and limitations

- **BLE Nordic UART Service (NUS):** transport code is included in `board_files/sdl/transport_ble_nus.py`. It is disabled in `config_default.py` and the example JSON. First qualify USB and Wi-Fi/TCP before enabling and testing it.
- **Browser dashboard:** not bundled in this historical release. Firefox does not expose standard Web Bluetooth directly; a Python Bleak/WebSocket gateway is a separate optional integration, as is a Chrome/Edge Web Bluetooth interface.
- **Normal host control:** `tools/sdl_client.py` speaks the SDL ASCII protocol. `tools/acceptance.py` checks basic status. The device is not a general-purpose TCP-accessible Python REPL; CRCL is the defined managed deployment path.
- **Untrusted code:** do not execute unknown programs. The CRCL integrity checks are not code signing, permission isolation, or network authentication.

## Regression tests and hardware acceptance

On a development PC run:

```powershell
py tests/run_all.py
py -m compileall -q board_files tools tests examples
```

The v1.1 release record says desktop tests passed; that result **does not prove the current physical Pico W setup works**. The acceptance checklist in `docs/ACCEPTANCE.md` proceeds from M0 (USB) through M8 (BLE), including deliberately interrupted transfer and power-loss recovery tests. Do not claim hardware qualification until those tests are performed and recorded on the actual device.

## When something goes wrong

| Symptom | Next check |
|---|---|
| `COMx` unavailable | Check USB cable/port, `mpremote connect list`, and close Thonny or other serial software |
| Pico not booting normally | BOOTSEL recovery and reinstallation of correct MicroPython UF2; first preserve any recoverable files |
| TCP does not connect | USB `INFO`, Wi-Fi SSID/password, node IP, host firewall, port 8765 and LAN connectivity |
| No `pb.*` devices | Confirm a real PicoBricks board and correct pin/profile configuration |
| Incomplete CRCL upload | Inspect `CRCL STATUS` then use the same app with `--resume` |
| Managed app fails health check | Inspect `APP STATUS`, rollback state and relevant failure artifacts; preserve resident runtime |
| BLE not visible | Expected until explicitly enabled; still needs real-hardware qualification |

## Safety, security, provenance

- GPIO is **3.3 V only**. HC-SR04 ECHO commonly requires level reduction; share grounds; check sensor supply voltage. See `docs/PICOBRICKS_QUICKSTART.md` and source README below for more detailed wiring notes.
- Keep the SDL TCP port on a trusted development LAN; do not forward it from your router. The configured token is plaintext and **not** production-grade authentication. No hostile-code sandbox is implemented.
- The historical `MANIFEST.sha256` was produced with the original v1.1 source, so the enhanced GitHub README will intentionally differ. Check file-level source provenance against the original ZIP before claiming reproducibility.
- The original release contains no explicit grant of a project-wide software license. Public visibility alone does not grant third parties permission to reuse code; settle licensing separately.

## Further documentation

- [`docs/INSTALL_MPREMOTE.md`](docs/INSTALL_MPREMOTE.md) — original deployment commands.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — resident components, logical roles, transport boundaries.
- [`docs/CRCL_PROTOCOL.md`](docs/CRCL_PROTOCOL.md) — transactional update protocol and recovery states.
- [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md) — M0–M8 bench checklist.
- [`docs/PICOBRICKS_QUICKSTART.md`](docs/PICOBRICKS_QUICKSTART.md) — board-specific devices.
- [`RELEASE_VALIDATION.md`](RELEASE_VALIDATION.md) — recorded desktop tests and open hardware tests.
- [`THIRD_PARTY_REFERENCES.md`](THIRD_PARTY_REFERENCES.md) — external references.

---

## Original v1.1 release details

The text below is preserved from the historical README for full feature and pin-level details.

# Pico W SDL/CRCL Reference Node v1.1

A resident, recoverable, remotely reprogrammable MicroPython laboratory node for Raspberry Pi Pico W and PicoBricks.

This project is the wireless/high-end member of the progression that began with the STC15W408AS 8051 SDL peripheral and continued through the Arduino Nano reference implementation. The permanent Pico W runtime owns transports, stable logical device roles, diagnostics, capability registration, and the CRCL updater. Experiment-specific behavior lives in a replaceable Python application and in late-bound capability packages.

**Release status:** software release candidate, desktop regression validated; physical Pico W/PicoBricks M0 acceptance still required.

## Implemented scope

- MicroPython resident runtime with a small `main.py` bootstrap.
- SDL ASCII Protocol 1.0-style request/response boundary over TCP port 8765.
- Human USB-console commands routed through the same command processor.
- Optional BLE Nordic UART Service transport; disabled by default for first bench bring-up.
- Stable logical-device registry.
- PicoBricks adapter:
  - red LED
  - RGB LED when `neopixel` is available
  - button
  - relay
  - buzzer
  - potentiometer
  - LDR
  - **automatic DHT11 / SHTC3 environmental-sensor selection** across PicoBricks revisions
- Hardware I2C scanner/read/write support on GP4/GP5 by default.
- MPU-6050 auto-detection at `0x68`.
- Optional HC-SR04 driver with temperature-corrected speed of sound.
- Optional DS18B20 driver using MicroPython `onewire` + `ds18x20`.
- Optional HX711 driver with interrupt-protected clock-high pulses.
- RP2040 internal temperature device.
- Late-bound capability registry with transactional package registration.
- Seed `demo_math` and `newton_cooling` capabilities.
- CRCL managed application deposition with:
  - fixed staging path
  - strict sequence numbers
  - two-slot CRC-protected transfer journal
  - pending-chunk intent record before every append
  - reboot reconciliation of full vs partial in-flight chunks
  - exact byte-count check
  - CRC32 verification
  - optional SHA-256 verification
  - `compile()` syntax preflight
  - active application backup
  - pre-promotion install marker
  - promotion
  - `health()` check
  - automatic rollback on failed activation
  - conservative boot rollback if reset occurs before install commit
- Desktop uploader with explicit resume after uncertain transport loss.
- Desktop acceptance and regression tests.

## Design rules

1. **Transport is not the language.** USB console, TCP, and BLE feed one command processor.
2. **Stable roles beat pins.** Experiments ask for `temp1`, `distance1`, `mass1`, `imu1`, etc.; wiring stays below that seam.
3. **No silent retry of uncertain physical operations.** If a command may have reached hardware, the host inspects state before deciding what to do next.
4. **Stage → verify → promote → health-check → commit.** Incoming code never overwrites the active application directly.
5. **Resident core and replaceable experiment code are separate.** The separation is architectural, not a security sandbox.
6. **Dynamic application code is trusted laboratory code.** It executes with interpreter privileges.
7. **Use battle-tested platform facilities first.** Hardware I2C, MicroPython 1-Wire support, `time_pulse_us`, and established sensor practices are preferred to unnecessary low-level reinvention.

## First bench target

For M0 physical acceptance, use:

- Pico W or PicoBricks with Pico W installed;
- USB cable for power, console, and deterministic rescue;
- Wi-Fi/TCP for normal SDL traffic;
- PicoBricks LED, button, potentiometer and LDR as the lowest-risk zero-wiring checks;
- PicoBricks environmental sensor if detected (`SHTC3` on newer revisions, `DHT11` on older revisions);
- CRCL dynamic update of `apps/crcl_app.py`.

BLE is already modularized, but leave it disabled until USB + TCP + CRCL pass acceptance.

## Install on Pico W

1. Install a current Raspberry Pi Pico W MicroPython UF2.
2. Copy the contents of `board_files/` to the Pico filesystem root.
3. Copy `config.picobricks.example.json` to `config.json`.
4. Edit `config.json` with the Wi-Fi SSID/password.
5. Reset the Pico.
6. Open the USB serial console.

Expected startup includes:

```text
Pico W SDL/CRCL Reference Node v1.1.0
Node: pico-sdl-bricks-01
Devices: ...
Capabilities: ...
SDL ASCII TCP: <ip>:8765
READY
```

If Wi-Fi is not configured or does not connect, the resident USB console still starts.

## USB console smoke test

```text
HELP
PING
INFO
DEV LIST
DEV READ pb.button
DEV READ pb.pot
DEV READ pb.ldr
DEV WRITE pb.led 1
DEV WRITE pb.led 0
DEV READ pb.env
I2C SCAN
CAP LIST
CAP CALL demo_add A=2.5 B=4
APP STATUS
CRCL STATUS
```

`pb.env` is present only when a supported PicoBricks environmental sensor is detected.

## TCP wire example

```text
CMD 101 PING
CMD 102 INFO
CMD 103 DEV.LIST
CMD 104 DEV.READ ID=pb.pot
CMD 105 I2C.SCAN
CMD 106 CAP.LIST
CMD 107 CAP.CALL NAME=demo_add A=2.5 B=4
```

Response shape:

```text
RSP 104 OK COUNT=1
DAT 104 DEVICE id=pb.pot model=PicoBricks-Potentiometer backend=hardware status=ok raw=32768 percent=50.0008
END 104
```

## Host acceptance

From the project directory:

```bash
python tools/acceptance.py 192.168.1.42
```

Use the address printed by the Pico USB console.

## CRCL dynamic application update

Push the included measurement application:

```bash
python tools/crcl_push.py 192.168.1.42 examples/crcl_app_measure.py
```

The uploader computes length, CRC32 and SHA-256, transfers Base64 DATA chunks with strict sequence numbers, asks the Pico to verify the staged file, then installs it.

If transport is lost after a DATA packet may have arrived, the uploader deliberately does **not** blindly resend that packet. Reconnect and run:

```bash
python tools/crcl_push.py 192.168.1.42 examples/crcl_app_measure.py --resume
```

### What v1.1 adds to recovery

Before each DATA append, the Pico records the sequence number, length and chunk CRC in a durable two-slot journal. On reboot:

- if no bytes landed, the same sequence remains pending for explicit resend;
- if the complete chunk landed and its tail CRC matches, the Pico commits it;
- if only part of the chunk landed, the staged file is repaired back to the last committed prefix.

Application installation has a second transaction boundary. An install marker is written before the active application is moved. If reset/power loss occurs before commit, the next boot conservatively restores the prior known-good application rather than trusting the candidate.

Rollback remains explicit:

```text
CMD 900 CRCL.ROLLBACK
```

## Optional external sensor rig

`config.sensor_rig.example.json` uses this example pin plan:

| Function | Pico pin |
|---|---:|
| I2C SDA | GP4 |
| I2C SCL | GP5 |
| HC-SR04 TRIG | GP14 |
| HC-SR04 ECHO | GP15 |
| DS18B20 DQ | GP16 |
| HX711 DOUT | GP17 |
| HX711 SCK | GP18 |

### Electrical cautions

- Pico GPIO is **3.3 V only**.
- HC-SR04 ECHO is normally a 5 V signal. Use a divider or level shifter before the Pico input.
- DS18B20 normally needs a 4.7 kΩ pull-up from DQ to 3.3 V.
- For HX711, use a breakout/power arrangement that does not present 5 V logic to Pico GPIO.
- Share grounds between connected modules.

## PicoBricks revision handling

The documented PicoBricks ecosystem includes older boards using DHT11 and newer boards using SHTC3 for temperature/humidity. v1.1 checks the I2C bus for a working SHTC3 at address `0x70`; if found, it exposes:

```text
pb.env
pb.shtc3
temp1   (unless an explicitly configured DS18B20 already owns temp1)
```

Otherwise it falls back to DHT11 and exposes:

```text
pb.env
pb.dht
temp1
```

This preserves the stable logical `temp1` role above the board-revision seam.

## Capability packages

A resident capability package is:

```text
capabilities/<package>/
    READY
    manifest.json
    module.py
```

`manifest.json` declares `apiVersion`, package `id`, `version`, `provides`, and required logical sensors. `module.py` exports:

```python
def register(registry, lab):
    registry.register("command_name", handler)
```

Registration is transactional: the package's promised command list must exactly match what it actually registers before its commands become visible.

**Scope boundary:** v1.1 dynamically transfers the managed application file `crcl_app.py`. Complete multi-file capability-package transfer over CRCL is a logical next feature, but is not claimed in this release.

## CRCL application contract

Managed `apps/crcl_app.py` may define:

```python
def health(ctx):
    return True

def setup(ctx):
    pass

def tick(ctx):
    pass

def stop(ctx):
    pass
```

`tick()` must return quickly. The resident runtime calls it frequently between transport polls. Repeated application exceptions stop the app rather than deliberately taking down the command server.

The context exposes:

```python
ctx.devices
ctx.lab
ctx.capabilities
ctx.emit(...)
ctx.now_ms()
```

This is an API boundary, not a security sandbox. A hostile or infinitely blocking application can still hang the interpreter.

## Validation status

Desktop validation performed for v1.1:

- all project Python files pass CPython compilation;
- SDL parser regression test passes;
- ordinary CRCL staged transfer, CRC/SHA verification, install and rollback test passes;
- full pending DATA chunk recovery simulation passes;
- partial DATA append repair simulation passes;
- latest-journal-slot corruption fallback test passes;
- interrupted application-promotion rollback simulations pass;
- SHTC3 command/CRC/conversion test passes;
- transactional capability registration test passes.

Still requiring physical M0 acceptance:

- actual Pico W MicroPython execution and free heap/filesystem margin;
- Wi-Fi behavior on the target network;
- PicoBricks polarity and device behavior on the user's exact board revision;
- SHTC3/DHT11 detection on the physical PicoBricks;
- BLE NUS interoperability with the chosen client;
- physical HC-SR04, DS18B20, HX711 and MPU-6050 wiring;
- real abrupt-power tests at multiple points in DATA append and application promotion.

Software recovery simulations increase confidence; they do **not** substitute for actual flash-filesystem power-cut testing.

## Next-level features after M0

The next release should prioritize:

1. Physical M0 acceptance and reproducible hardware-in-the-loop regression.
2. BLE/NUS qualification as a second first-class transport.
3. Transactional CRCL deployment of complete multi-file capability packages.
4. Signed/curated package manifests and stronger administrative authorization.
5. Watchdog-assisted safe boot and repeated-crash rollback.
6. Browser management dashboard for inventory, telemetry, deployment and diagnostics.
7. Multi-node discovery through the PC SDL Gateway/MCP layer.
8. Optional RP2040 PIO backends for timing-sensitive laboratory interfaces.

