# MSP430 cooling acquisition application (NEW integration)

The **original archive** is in `../original/msp430/`; its bytes are unchanged. New `cooling_main.c` adds an experiment command receiver, sampling-complete GPIO marker, and reports the *same original raw evidence format* expected by the integration program. `vendor/` contains byte-identical copies of six original modules for portable compilation.

## Build using Code Composer Studio / MSP430G2553

1. Create a new MSP430G2553 **empty C project** with an appropriate MSP430G2553 linker command file.
2. Add `cooling_main.c`, `vendor/09_onewire_transport_CANDIDATE.c`, `vendor/12_sensor_evidence.c`, and `vendor/06_ds18b20_decode.c` as the **four C translation units**. The remaining `.h` files are included by the source; **do not add the original `13_integrated_lab_CANDIDATE.c`** (it has another `main`).
3. Use 1 MHz calibrated DCO, 3.3 V signal levels, and compile for the **actual** MSP430G2553 target. Upload via your eZ-FET, not through the Pico.
4. Test P1.7 reset/write/read slot waveforms with a scope/logic analyzer before accepting DS18B20 measurements.
5. Starting this app is safe with unpowered load outputs: P1.0/P1.6 are LED demonstration signals only.

## Electrical connections

- DS18B20 VDD=3.3V, GND=GND, DQ=P1.7 **with external 4.7k pull-up to 3.3V**. Do not use parasite power. Only *one* 1-Wire sensor on this bus.
- MSP430 P1.2 TXD -> Pico GP1 UART0 RX.
- MSP430 P1.1 RXD <- Pico GP0 UART0 TX.
- MSP430 P2.0 sampling-complete output -> Pico GP2 timing input (optional but recommended).
- MSP430 GND <-> Pico GND. Power each board using its intended supply. Do not join the 3.3 V output rails without a power design.
- Optional P1.7 DS18B20 data -> Pico GP3 **input-only** for PIO pulse observer, all signals 3.3 V.

## Timing limitations

The conversion-wait interval is **nominal** and not independently tested. The `period_ms` setting targets the delay between starts only approximately: transaction overhead and reporting add time. The Pico measures the *observed* intervals using GP2. The marker represents **end of acquisition**, not the DS18B20's internal sample timestamp. At 12-bit resolution, conversion can take up to 750 ms.

## Commands from Pico

`START`, `STOP`, `PING`, `RATE=1000` (range 1000..60000 ms), `FAULT=0`, `FAULT=1` (deliberate CRC corruption), `FAULT=2` (deliberate missing sample). Newline terminates every command. `STOP` takes effect after any ongoing conversion (up to ~750ms), and sampling may complete once after a command. State the limitation to students.

### Status

Integration code is an implementation **candidate**, not verified as compiled/flashed on a physical MSP430. Physical electrical, timing, temperature, and serial results must be collected on the actual target.
