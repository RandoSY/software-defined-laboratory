# UNO Q Spirit acceptance and fault-injection test plan

**Do not plug in the original 5 V Spirit shield until the electrical work is complete.**

## Stage A: unpowered hardware inspection

- [ ] Obtain source KiCad schematic/PCB, exact revision and every header's pin-1 orientation; compare with historical PDF pin map.
- [ ] Check no short 3V3-to-GND, 5V-to-GND, 3V3-to-5V or terminal-to-USB VBUS.
- [ ] Map D2–D9 and A4/A5 to actual connectors with meter, record net names.
- [ ] Verify HC-SR04 type: use real 3.3 V echo output or certified level translator at D8.
- [ ] Check HX711 module VCC/VDD/DOUT and load-cell excitation; I²C 0x39 breakout's regulator/pullups.
- [ ] Validate buzzer is an active 3.3 V compatible module/driver, not raw inductive load.

## Stage B: powered independent carrier verification

- [ ] Use current-limited bench source, **without UNO Q attached**. Measure every rail.
- [ ] Verify 3.3 V SDA/SCL idle with calibrated DMM; no 5 V pull-ups.
- [ ] Inspect D7 trigger and D8 translated echo with scope (UNO Q input must never see >3.3 V nominal).
- [ ] Verify HX711 SCK high pulse widths remain below chip's unintended power-down threshold (~60 µs).
- [ ] Check DS18B20 pull-up at 3.3 V, cable length and signal integrity.
- [ ] Verify no external power backfeeds USB-C or the original host supply.

## Stage C: MCU + Bridge validation

- [ ] Capture Arduino IDE Verify output, board core version, libraries, sketch RAM/flash size.
- [ ] Boot with NO sensors and confirm `mode=synthetic`, all four `state=SYNTH` and changing values.
- [ ] Stop Linux `arduino-router` and confirm STM32 acquisition continues (requires a monitored test setup).
- [ ] Enter live after electrical gate; remove each individual sensor and confirm `MISSING` or `TIMEOUT`, no crash/reset.
- [ ] Reattach sensors and confirm successful recovery within suitable retry periods.
- [ ] DS18B20: compare 0°C ice bath, ambient and modest warm points; CRC errors must not appear as valid temperatures.
- [ ] HX711: vary calibrated masses, tare, calibrate and repeat; check count noise under still and moving conditions.
- [ ] HC-SR04: compare ruler positions at 5, 10, 20, 50, 100, 200 cm; measure pulse width and timeout.
- [ ] AS7343: validate chip ID at 0x39, vary gain 0–12, inspect saturation and 18-slot mapping under known light sources.
- [ ] Measure command round-trip response, loop jitter, and spectral read blocking under disconnect/reconnect.
- [ ] Keep sensor current and CPU/thermal budget within UNO Q specifications.

## Pass/fail protocol

Record test date, source commit, exact UNO Q OS/core build, sensor module part/revision, supply voltage, instrument model, expected vs actual readings, waveform screenshots and acceptable tolerance agreed before test. Mark FAIL rather than omitting missing data. No stage C functionality can be promoted to VERIFIED based on synthetic mode alone.
