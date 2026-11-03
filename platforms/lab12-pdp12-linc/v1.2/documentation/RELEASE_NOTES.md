# LAB-12 1.2 Release Notes

## Additions in 1.2

- Dedicated **Precision graph** tab is now the default operator view, leaving
  the original experiment, instrument, data and guide tabs intact.
- Large high-DPI live graph with physically correct elapsed-time and °C axes,
  rolling or full-run windows, automatic or manual Y-axis bounds.
- Pico-provided model overlay, ambient baseline, residual plot, event markers,
  bad-sample crosses, and line discontinuities for invalid/missing records.
- Crosshair chooses the nearest *real recorded sample*; displays raw
  evidence quality, clock provenance and values.
- Hold time window without halting acquisition/CSV; export graph PNG.
- Chrome browser smoke-tested with 120 injected synthetic JSON observations;
  no physical hardware verification claimed.

## Completed in this source package

- Original MSP430 archive preserved byte-identically.
- Separate MSP430 integration C source using copied original modules.
- Pico W MicroPython instrument firmware, CRC validation, sampling interval
  statistics, bounded experiment memory and history replay.
- Pico-resident Newton cooling k / tau / RMS calculation, programmable ambient,
  fit enable/disable and autonomous falling-temperature event.
- Offline one-file Chrome dashboard with direct USB Web Serial, scaled live
  temperature plot, residual chart, operator administration, events and logs.
- CSV snapshot export, operator-selected incremental CSV file recording,
  separate events CSV and metadata JSON; no Wi-Fi or Python bridge.
- Eleven host unit tests, plus JavaScript syntax check.

## Not verified / not implemented

- No physical MSP430 or Pico W flashing, serial acquisition or 1-Wire signal
  timing verification; board results must be collected by operator.
- No target MSP430 C compiler available for new `cooling_main.c`.
- No confirmed Chrome hardware Web Serial session in this environment.
- No cycle-accurate LINC/PDP-12 emulator or instruction-set implementation.
- No Pico PIO 1-Wire pulse-width analyzer; GP2 is a soft-IRQ event marker.
- No autonomous file storage on Pico flash; use authorized browser CSV.

## Near-term extension path

1. Verify one-wire reset/read/write timing and target compile.
2. Attach acquisition-complete GPIO marker and compare timestamps.
3. Add a dedicated RP2040 PIO pulse-timing instrument on an *input-only* probe
   lead, then calibrate it against a known pulse source.
4. Add optional onboard experimental programs for multiple temperature
   interventions without making Chrome responsible for scientific control.
