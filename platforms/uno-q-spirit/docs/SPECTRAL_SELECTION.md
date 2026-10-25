# Spectral sensor selection and fidelity plan

**Engineering review date:** 2026-10-25 · **Status:** no calibrated optical measurements yet.

## Important newer option

The first firmware target is the **Adafruit AS7343 14-channel breakout (#6477)**, published in March 2026. This is a valid, actively supported sensor, but **it is no longer the newest Adafruit 14-channel spectral breakout**: Adafruit published the **TCS3448 (#6525)** breakout and library in September 2026.

| Property | AS7343 (#6477, firmware v0.1.1 target) | TCS3448 (#6525, future alternative) |
|---|---|---|
| Supplier / designer | Adafruit breakout / ams OSRAM die | Adafruit breakout / ams OSRAM die |
| I²C address | **0x39** | **0x59** |
| Arduino library | `Adafruit_AS7343` | `Adafruit_TCS3448` — **not** drop-in |
| Channels | 11 overlapping visible bands + NIR + clear + flicker, via SMUX | Same broad family/14-channel class, retuned interference filters |
| Typical wavelength coverage | Channel centers roughly 405–855 nm; response extends wider | 11 visible bands across ~380–800 nm plus NIR centered ~855 nm, response approaching 1000 nm |
| Published improvement | Mature source and existing UNO Q Spirit integration | Better responsivity in several violet/blue and far-red channels; **lower NIR sensitivity** reported |
| Live verification | **Not performed** | **Not performed** |

The TCS3448 is ams OSRAM's designated successor to the AS7343. Its published datasheet and Adafruit overview report retuned channel responses, not a universal signal-to-noise improvement. A new or newer part is not automatically the most faithful choice for every measurement.

## Recommendation for the prototype

**Keep AS7343 #6477 as the firmware's current sensor target** so the first bring-up has one definite implementation and testable I²C address. If a **TCS3448** has already been purchased, do **not** connect it expecting current AS7343 code to work. It needs the separate driver and firmware integration, including address and channel metadata changes.

The spectral optical responses are **broad and overlapping bands**; neither breakout is a continuously wavelength-scanning spectrometer, and the 18 SMUX readout positions are not 18 independent calibrated wavelengths.

## How to judge maximum fidelity

1. Fix illuminator, sample geometry, warm-up, distance, supply voltage and ambient conditions.
2. Capture dark/covered readings; quantify offset and noise for each channel.
3. Sweep **gain** and **integration time** (integration-time CLI control is not implemented in firmware v0.1.1; changing source/rebuilding is required).
4. Discard saturated readings and those close to 16-bit limits; plot channel mean, standard deviation, and fraction of clipped frames.
5. Capture multiple light standards, ideally a spectrometer-calibrated reference; compare repeatability and sensitivity, not arbitrary raw counts.
6. To compare AS7343 vs TCS3448, use each sensor's **own gain, integration, calibration factors and band response curves**. Do not compare raw counts as though the devices had identical responsivity.
7. Measure the *actual* elapsed sampling time and Zephyr scheduling jitter on UNO Q. Adafruit's synchronous read function can wait up to approximately 1 s for data readiness, which means this sketch is not a hard real-time spectrometer.

## Official references

- [Adafruit AS7343 product guide](https://learn.adafruit.com/adafruit-as7343-14-channel-light-color-sensor-breakout)
- [Adafruit AS7343 Arduino library](https://github.com/adafruit/Adafruit_AS7343)
- [Adafruit TCS3448 guide and comparison](https://learn.adafruit.com/adafruit-tcs3448-14-channel-light-color-sensor-breakout)
- [Adafruit TCS3448 product #6525](https://www.adafruit.com/product/6525)
- [ams OSRAM AS7343 sensor and TCS3448 replacement](https://ams-osram.com/products/sensor-solutions/ambient-light-color-spectral-proximity-sensors/ams-as7343-spectral-sensor)
- [ams OSRAM TCS3448 sensor](https://ams-osram.com/products/sensor-solutions/ambient-light-color-spectral-proximity-sensors/ams-tcs3448-spectral-color-sensor)
