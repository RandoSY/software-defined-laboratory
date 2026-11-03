# LAB-12 — PDP-12 / LINC-Inspired Digital Cooling Laboratory

**Release 1.2 — Source compilation / pedagogical engineering prototype**

The goal is to reconstruct the laboratory-computing *idea* of DEC's LINC and
PDP-12, not to emulate their historical opcodes. Here the RP2040 Pico W is the
programmable experiment computer, the MSP430G2553 is the dedicated physical
acquisition/control subsystem, and Chrome is a display, data-management and
administrative station. The instrument works with USB, **not Wi-Fi**, and
requires no PC-side Python serial bridge.

> **Compilation, not replacement.** `original/ORIGINAL_msp430.zip` is a byte-for-
> byte copy of the user's `msp430.zip`; `original/msp430/` is its unmodified
> expanded source tree. New code is located in `msp430_new/`, `pico_w/`,
> `dashboard/`, `tests/`, and `documentation/`. Do not edit the original tree.

## Quick-start, first without hardware

1. Extract this ZIP, preserving directory structure.
2. Open **`dashboard/lab12_dashboard.html` in Google Chrome** (use Open with → Google Chrome if Firefox is default).
3. Select the **Lab guide** tab and click **Start simulated experiment**; it opens the new **Precision graph** tab.
4. Explore the enlarged elapsed-time plot, selectable time and °C scales, crosshair, model overlay, residuals, and Data / CSV exports.
5. The DEMO badge and `DEMO_ONLY` record quality explicitly mark synthetic data.

This verifies the user interface without claiming physical measurement or
validating firmware on a board.

## Hardware run

1. Connect the 3.3 V hardware per `documentation/WIRING.md`.
2. In TI Code Composer Studio, create an MSP430G2553 empty C project and add
   the **four C files** listed in `msp430_new/README.md`. Build and program it
   using the MSP430 debugger. **Do not add 13_integrated_lab_CANDIDATE.c**; the
   new application has its own `main()` and uses original support modules.
3. Install MicroPython on your **Pico or Pico W**. Using Thonny (or equivalent),
   copy `pico_w/protocol.py`, `pico_w/labcore.py`, and `pico_w/main.py` to the
   board's root. `main.py` starts on reset. Close Thonny afterward so it does
   not monopolize the USB serial port.
4. Open the single-file dashboard in **Chrome**. Click **Connect USB** and
   select the Pico's USB serial device (not the MSP430's debug console).
5. Click **Status** and look for a `LAB12_PICO_W` status reply. If the MSP430
   is connected, `START` will request sensor readings; **first set ambient**
   using a separate thermometer and **Apply settings**.
6. Press **Record to file** to select your own CSV path; Chrome writes the
   data during the experiment. Or press **Export CSV** for a snapshot.
7. Use **LINC instrument → Arm crossing** to let the Pico independently detect
   and record a falling temperature threshold even if the browser disconnects.
8. Stop, close the CSV recording stream, export event CSV and session metadata
   JSON (which contains your run notes), and retain all three files together.

## What runs where

| Computer | Hardware and operation | Evidence preserved |
|---|---|---|
| DS18B20 | Physical temperature conversion | 9 scratchpad bytes |
| MSP430 | 1-Wire bus, conversion request, CRC checking, simple GPIO demonstration, UART evidence | Sequence, signed raw x16, status, ROM and scratchpad |
| Pico W, MicroPython | Observe acquisition marker, independently re-check ROM/scratch CRC, detect missing/duplicate observations, retain 160 readings in RAM, calculate sampling jitter, **fit Newton's model**, mark physical events, detect threshold crossings | Timestamp type, interval stats, quality flags, residual, cooling k and τ, RAM history |
| Chrome Web Serial | Dedicated Precision graph tab with time/temperature scales and hover inspection, operator controls, live plots, residual plot, tabbed navigation, notes, CSV export and on-disk recording, log/history retrieval | Full run CSV, events CSV, metadata JSON (only after operator saves them) |

The Pico is **not** an RP2040-based bit-banging substitute for the MSP430's
1-Wire implementation. It provides second-opinion instrumentation and the
experiment's computational and programmed control layer.

## Experiment program on Pico

The educational cycle is defined in `pico_w/labcore.py`:

```
ACQUIRE  ->  VALIDATE  ->  STORE  ->  ANALYZE  ->  PUBLISH
(MSP430)     (Pico)       (Pico)     (Pico)      (Pico USB)
```

This is a **laboratory workflow**, not a PDP-12/LINC instruction emulator.

The Pico supports command-programmed RATE, AMBIENT, FIT, and falling TRIGGER;
experiment events are timestamped and recoverable after a USB reconnection
(within the 160-item memory window). Its RAM is volatile. The browser is the
persistent experiment recorder, a deliberate separation analogous to an
operator station and mass storage.

## Important limitations

- Hardware behavior **has not been tested on physical MSP430 or Pico** in this
  release. Original modules with `_CANDIDATE` in the filename remain candidates.
- Original archive compilation artifacts do not establish that the new
  integration firmware compiles or works on the target. A board build is still
  required; there is no MSP430 cross compiler available in this environment.
- The 1-Wire timing on P1.7 must be checked using real hardware. The optional
  P2.0 marker goes high **after capture**, not when temperature physically
  changes. GP2 MicroPython soft-IRQ timestamps are not nanosecond measurements.
- Our Pico log-linear cooling fit assumes fixed ambient, adequately mixed
  sample, approximately first-order heat transfer, and the subset of valid
  readings with T > ambient + 0.5 °C. It is not a calibrated metrology model.
- Pico RAM is bounded at 160 observations. **Save the CSV in Chrome** for long
  experiments. Chrome does not write CSV automatically until you authorize
  a file. Notes and final fitted parameters are preserved in the metadata JSON.
- The MSP430 thermostat-style P1.0/P1.6 outputs are demonstrator LEDs only.
  Do not connect a mains, heater or other consequential load to this teaching code.
- Live file recording uses Chrome's File System Access API. If unavailable,
  use **Export CSV**. Keep the page running during acquisition; loss of USB
  connection means no continuous CSV capture until it reconnects.

## Test status

`python -m unittest discover -s tests -v` tests core protocol/analysis under
CPython without hardware. `node --check` of the dashboard's embedded JS was
successful. These are **host tests**, not target-build or bench-test evidence.

## Contents

- `original/`: unmodified upload including original `.zip`, all CCS projects,
  documentation and original SHA-256 manifest.
- `msp430_new/`: minimal separate cooling acquisition app and references to
  original source copied byte-identically into `vendor/` for compilation.
- `pico_w/`: `protocol.py` (sensor evidence), `labcore.py` (experiment computer),
  `main.py` (hardware, timing, operator protocol and orchestration).
- `dashboard/`: `lab12_dashboard.html`, one self-contained offline dashboard; new dedicated full-size Precision graph tab.
- `documentation/PRECISION_GRAPH_GUIDE.md`: detailed explanation and student code tour of the graphing instrumentation.
- `tests/`: portable host-side unit tests.
- `documentation/`: wiring, protocol, experiment & teacher guide, concept mockup.

## Origin and inspiration

Original DEC PDP-12 User Handbook, 1969. This project translates its integrated
measurement, display, programmable laboratory clock and operator-console
philosophy onto independent microcontrollers and a modern browser. This is a
new instructional reinterpretation, **not a replica** of historical hardware.

## 1.2 display upgrade

The **Precision graph** is now a dedicated, default tab. It adds an enlarged
real-time chart, true elapsed-time and temperature scales, rolling/fixed
windows, manual °C limits, marker overlays, a nearest-measurement crosshair,
residual panel, and PNG plot export. The pre-existing **Experiment control**,
**LINC instrument**, **Data / CSV**, and **Lab guide** tabs are retained.
The original acquisition and Pico W MicroPython files are unchanged. See
`documentation/PRECISION_GRAPH_GUIDE.md` for controls, teaching uses, and
scientific limits.