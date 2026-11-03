# LAB-12 v1.2 archival status — 2026-11-03

## Public GitHub source status
This directory preserves the author's LINC/PDP-12-inspired cooling lab as a **source-level teaching prototype**. It uses:
- MSP430G2553: DS18B20 1-Wire acquisition and timestamped evidence through UART.
- Pico/Pico W (MicroPython): experiment control, validation, event capture, cooling-model fit and buffered data.
- Chrome Web Serial: live full-size precision graph, residuals, administration and operator-approved CSV exports.

**Published from the November 2 original compilation:** release README, release manifest, Chrome dashboard and launch helper, precision graph guide, release notes, teacher/operator guide, wiring, MSP430 application, MicroPython programs and host tests.

**Outstanding:** the `documentation/PROTOCOL.md` source has not been committed in this directory; it remains within the separately retained original ZIP. The *complete* original 409-entry compilation, including the unmodified historical source archive, is not yet a GitHub binary release. Two Markdown/HTML files here were initially transferred with a one-byte difference in line-ending/final-newline handling; do not call them byte-identical without checking their original ZIP entries.

## Original artifact identity
`LAB12_PDP12_LINC_Cooling_Lab_Compilation_v1_2.zip`:
- 3,396,254 bytes
- SHA-256: `2f7e3ab946e3e495895293abf5c1a3dcd063c87bae75fa88356a1c9078fce381`
- 409 ZIP entries

The complete source ZIP is retained in the owner's archive; this status file is **not** a replacement for its contents. See the [Project Atlas preservation baseline](https://github.com/RandoSY/project-atlas/blob/main/baselines/CORE10_CORE12_PUBLIC_PRESERVATION_BASELINE_2026-11-03.md).

## Tests independently rerun from original ZIP — 2026-11-03
Command: `python -m unittest discover -s tests -v`.

**11 host tests passed**, covering ambient range, bounded memory, duplicate/missing observations, event recording, Newton fit, injected faults, CRC and signed temperature decode. These results apply to CPython host tests, **not** an independently proven MSP430 target build or Pico/DS18B20 hardware run.

Original release explicitly records that physical board integration, 1-Wire timing and target builds remain unverified. Model fit and sample timestamps are instructional, not precision-calibrated metrology. Do not use demonstrator LED outputs to drive mains or consequential loads.

## Archival policy
Retain this version as a historical point-in-time source edition. Future hardware-tested versions should be additive releases with build results, actual sample CSV, metadata JSON, wiring photos and a reproducibility note. Neither original experiments nor previous editions should be silently replaced.
