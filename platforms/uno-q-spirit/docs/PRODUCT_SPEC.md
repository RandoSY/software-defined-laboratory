# Engineering Product Specification — UNO Q Spirit Instrument Verification

**Document:** UQS-SPEC-001  |  **Release:** 0.1.1-prototype  |  **Date:** 2026-10-25  |  **Status:** Engineering preview, not hardware released

## Product mission

UNO Q Spirit is an STM32U585-based educational lab card validation platform that samples ultrasonic distance, force/weight, temperature and multispectral light. The Arduino sketch is the safety-critical acquisition endpoint; Qualcomm Linux is an OPTIONAL command/data consumer, not necessary for continuing sensor acquisition after initial firmware initialization. The project is an advanced optional instrument within the Software-Defined Laboratory ecosystem.

## Two-sensor prototype configuration

For initial validation on an ordinary unpopulated Arduino prototype shield, `profile prototype` limits live acquisition to **DS18B20 D2** and **AS7343 on UNO Q `Wire` D20/D21**. HX711 and ultrasonic report `DISABLED` and are not polled. `profile all` restores four-sensor acquisition. This is tested in the desktop simulation, **not yet validated on UNO Q hardware**. See [prototype quickstart](PROTOTYPE_SHIELD_QUICKSTART.md).

## Operational modes

| Mode | Requirements | Actual v0.1 implementation |
|---|---|---|
| Synthetic | Starts by default; no sensors required; continuously varies all channels; real sensor addresses not contacted during synthetic setup | IMPLEMENTED, unit / host mock tested |
| Live | Entered only by explicit RPC command; supports absent sensors and retries; no single missing sensor terminates acquisition | IMPLEMENTED, simulated missing-sensor path tested |
| Paused | `stop` halts samples without shutting down the Bridge; `start` resumes | IMPLEMENTED, host simulated |
| Interactive | Linux Python shell forwards CLI commands using native Arduino RouterBridge | IMPLEMENTED, host test; actual router not tested |
| Records | Python CSV capture of raw/filtered state, status and 18 spectral register slots | IMPLEMENTED and host tested |

## Requirements

| ID | Normative requirement | Acceptance evidence | Current status |
|---|---|---|---|
| FR-01 | Preserve historic D2–D9 pins; clearly distinguish historic A4/A5 I²C from current UNO Q `Wire` D20/D21 | PDF audit & pin contract | Documented; native PCB unverified |
| FR-02 | Handle missing/failed sensors without exceptions, infinite waits or acquisition halt | Absent-sensor simulator & bench disconnections | Mock passed; hardware pending |
| FR-03 | Produce variable synthetic data for all four sensor families without any connected sensor | Python and C++ harness | Passed |
| FR-04 | DS18B20 temperature via 1-Wire, ROM/scratchpad CRC, asynchronous 12-bit conversion | Oscilloscope + controlled-temp comparison | Code present; hardware pending |
| FR-05 | HX711 signed 24-bit samples, tare, calibration against known mass, raw count variance | Certified weights, clock timing | Code present; hardware pending |
| FR-06 | Ultrasonic burst, echo timeout and Celsius-compensated distance | Ruler targets 5–200 cm, timeout | Code present; hardware pending |
| FR-07 | AS7343 I²C 0x39 identification, 18-slot SMUX read, adjustable gain and saturation detection | Known light sources, gain sweep, spectral repeats | Code present; hardware pending |
| FR-08 | Bridge RPC commands and status JSON via Python CLI and CSV export | End-to-end physical IAS-Q | Host mock passed; actual bridge pending |
| FR-09 | Fault/status taxonomy: SYNTH / WARMUP / OK / MISSING / TIMEOUT / FAULT / SATURATED | Sensor detach/reconnect | Mock passed for missing; other cases pending |
| FR-10 | Bounded scheduling; no sensor data claimed as calibrated without explicit calibration | Measured worst-case latencies and jitter | Partial: blocking pulseIn <=30 ms; AS7343 driver 1 s wait; physical scheduling pending |
| FR-11 | Linux-side Bridge failure must not stall local sampling | Disconnect Linux router during STM32 run | Separate Zephyr bridge init thread implemented; hardware pending |
| FR-12 | Safe 3.3 V hardware and no power backfeed | Schematic/ERC/DRC, oscilloscope/DMM | NOT SATISFIED; must redesign original 5V PCB |
| FR-13 | Reproducible UNO Q Arduino IDE compile/upload | UNO Q board/core version + compile logs | NOT RUN — unavailable compiler/runtime in execution environment |
| FR-14 | Source and tests published under version-controlled directory | Commit URL and manifests | Publication pending completion of GitHub operation |

## Timing and numeric model

- HX711 polling: 125 ms, not an assurance of 80 samples/s. Actual throughput is limited by the module's mode and the code's polling interval.
- Ultrasonic: 300 ms, 30,000 µs maximum echo wait (`pulseIn` is blocking). Distance computed using `speed_mps = 331.3 + 0.606 * temperature_C`; defaults to 20°C when measured temperature unavailable. Nominal accepted range 2–400 cm.
- DS18B20: 1,000 ms initiation period, 750 ms nonblocking conversion delay; CRC-checked. Power-on 85°C sample is rejected as ambiguous and retried.
- AS7343: 2,000 ms acquisition interval, startup integration `ATIME=29`, `ASTEP=599`, gain code `6`/64x; Adafruit's readAllChannels includes up to 1,000 ms wait, so this release is **not hard-real-time verified**.
- Synthetic: 1,000 ms report generation default (configurable 100–10,000 ms). Synthetic values are NOT metrological calibration evidence.
- Filtering: RunningStat uses online Welford mean/sample standard deviation for HX711 counts, ultrasonic cm and sketch-loop interval. Numeric invalid values rejected, stale sensor values suppressed as JSON null for non-OK states.
- Spectrum: the 18 readout slots are counts, **not wavelength-calibrated radiometric power**; only gains are user-configurable in this release. Saturation is flagged.

## Error behavior and limits

Missing HX711: DOUT never ready -> TIMEOUT, rest of sketch continues. Missing HC-SR04: bounded echo -> TIMEOUT. Missing DS18B20: ROM/presence absent -> MISSING. Missing AS7343: address not acknowledged -> MISSING. Faulty I²C backend timeout behavior and Zephyr interruption effects still require real tests. A failed bridge `Bridge.begin()` runs on an independent Zephyr thread but can consume that thread; it does not terminate acquisition.

### Known preview constraints

1. Not compiled against real UNO Q board package: build/API compatibility still a gate.
2. No live hardware or current/voltage safety test. No redesigned KiCad project.
3. No absolute timing guarantees and no measured Zephyr priority/inversion/jitter limits; sensor work shares one Arduino loop.
4. Bus reinitialization and module-specific I²C bus faults may have long backend timeouts; requires physical fault injection.
5. Power-off/signal backfeeding, input protection and external connector safeguards are hardware design responsibilities.
6. HX711 calibration stored in volatile RAM, not retained after resets; gain configuration also not persistent.
7. No continuous buffered 80 SPS acquisition, interrupt-driven echo, flicker-frequency processing or full optical radiometric calibration at this version.
8. Synthetic test acceptance does not imply live calibration accuracy.

## Release gates

- **Software candidate:** pure C++ unit tests, Arduino-sketch host compilation and Python tests pass — **PASSED**.
- **Arduino image integration:** Arduino CLI compilation and upload to actual UNO Q — **PENDING**.
- **Electrical safety:** revised shield continuity/rails/level compatibility — **PENDING**.
- **Real sensors:** connect/disconnect, accuracy, noise and saturation characterization — **PENDING**.
- **Production ready:** **NOT AUTHORIZED**.
