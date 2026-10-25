# Original AVR Spirit pin contract and UNO Q electrical migration

**Primary evidence:** `Nugget_2Wire_Sensor_Shield_KiCad_Autorouting_Programmers_Guide.pdf` (user document), pp. 2, 4–6. This is a historical **v0.2x** guide, and the last native KiCad project has not been compared. Pins may differ in a later CAD revision.

| UNO Q header | Historical PCB net | MCU mapping documented in user-provided UNO Q redesign brief | Requirement for future Spirit board |
|---|---|---|---|
| D2 | D2_ONEWIRE / DS18B20_DATA | PB3 | 3.3 V one-wire, 4.7 kΩ pull-up to 3.3 V |
| D3 | HX711_DT | PB0 | No DOUT level higher than MCU IO domain |
| D4 | HX711_SCK | PA12 | HX711 clock verified at 3.3 V |
| D5 | D5_START | PA11 | Input pullup to 3.3 V, switch to GND |
| D6 | D6_TARE | PB1 | Input pullup to 3.3 V, switch to GND |
| D7 | D7_TRIG | PB2 | 3.3 V compatible ultrasonic trigger |
| D8 | D8_ECHO | PB4 | **Must level translate 5 V echo** or use verified 3.3 V module |
| D9 | D9_BUZZER | PB8 | **Active buzzer MODULE signal only**, not raw speaker |
| A4/D18 | SDA | PC1, I2C3 | 3.3 V I²C SDA and pull-ups |
| A5/D19 | SCL | PC0, I2C3 | 3.3 V I²C SCL and pull-ups |
| 3V3/GND | Previously +5V/GND | — | Power from protected 3.3 V sensor rail; current budget |

Arduino's full pinout: https://docs.arduino.cc/resources/pinouts/ABX00162-full-pinout.pdf. **Verify** physical pin descriptions and `Wire` defaults against the installed Arduino UNO Q core prior to wiring.

## Stop/no-go conditions

- Unmodified historical 5-V Spirit shield connected to UNO Q before checking every GPIO net.
- Any HC-SR04 ECHO at 5 V presented to an unverified D8 input, especially with analog mode or MCU unpowered.
- Any 5 V external I²C pull-up or bare AS7343 connected directly without its breakout's voltage regulation/level shifting.
- Any unregulated external screw-terminal voltage directly into 3V3 or 5V power pins.
- Any simultaneous unisolated terminal/USB-C power sources creating reverse current paths.
- Any module pin order assumed without continuity test from schematic/netlist to real connector.

## Spectral breakout

Selected **Adafruit AS7343 14-Channel breakout #6477**, I²C address **0x39**, onboard 3–5 V VIN regulation and level shifting per Adafruit. The `AS7343_SMUX_18CH` API returns **18 raw register slots**, not 18 independent visible-light wavelengths. It contains repeated clear-channel measurements and muxed spectral channels; consult the `Adafruit_AS7343.h` channel enumeration when interpreting the data. Spectral peak wavelengths span roughly 405–855 nm; the measurement range is not broadband true spectrometer resolution. The module has 100/120 Hz flicker detection facilities, not implemented as a frequency spectrum in this release.

Adafruit sources: https://www.adafruit.com/product/6477 , https://learn.adafruit.com/adafruit-as7343-14-channel-light-color-sensor-breakout/pinouts , https://github.com/adafruit/Adafruit_AS7343

## Unverified electrical details

This firmware establishes the logical pin contract but no electrical adaptation has yet been made to the user-built shield. **Manufacturer layout, resistor networks, pull-ups, voltage regulators and actual connector orientations have not been inspected.** The KiCad file/BOM plus meter tests are required before declaring the daughterboard compatible. No claim of firmware operation on a real sensor is made here.
