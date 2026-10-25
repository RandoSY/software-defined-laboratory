# UNO Q Spirit — two-sensor prototype-shield bring-up

**Engineering test procedure UQS-TP-01 • 2026-10-25 • Electrical + firmware validation pending**

## Purpose and scope

Build a small, reversible test on an **unpopulated Arduino UNO-style prototype shield or solderless breadboard**. There is **no need to manufacture or modify AVR Spirit** for this first experiment. Use only:

1. **DS18B20** (3-wire, externally powered) on D2, checking OneWire timing/CRC;
2. **Adafruit AS7343 breakout #6477** on the UNO Q's **default `Wire` bus (D20/D21)**, checking 18-slot multispectral measurements and gain controls.

The HX711 and HC-SR04 are deliberately **not connected**. Firmware command `profile prototype` stops their acquisition attempts and reports `DISABLED` rather than accumulating irrelevant timeouts. D5/D6 buttons and D9 buzzer are optional and may remain empty. Start in synthetic mode; enter live mode only when wiring is electrically checked.

## Critical distinction: original AVR Spirit pin assignment vs UNO Q Wire

The historic 5 V Nugget/AVR Spirit PDF assigns **I²C to A4/A5**. Arduino's official **UNO Q** user manual specifies **`Wire` on D20 (SDA, PB11) and D21 (SCL, PB10)**. A4/D18 (PC1) and A5/D19 (PC0) are a *different* STM32 I²C3-capable pair; they do **not** connect to `Wire` by default. This prototype's current firmware calls `Wire.begin()` and `as7343.begin(..., &Wire)`, so **wire AS7343 to D20/D21, NOT A4/A5**. This is an intentional temporary bus change, not an undocumented reworking of the original netlist.

ArduinoCore-zephyr has also introduced `Wire2` support for A4/A5 in newer releases, but the installed board package's exact support must be verified before changing code. Using the physical Qwiic socket requires `Wire1.begin()` and passing `&Wire1` to the AS7343 library; the unmodified Spirit sketch is **not** configured for that Qwiic bus.

**Want to test only the spectrometer?** Use the [standalone AS7343 Qwiic example](../examples/as7343-qwiic-test/README.md): plug the AS7343 STEMMA QT cable into the UNO Q Qwiic socket (or use four jumper wires on D20/D21); the independent sketch auto-detects either bus and prints spectral counts in Serial Monitor. This path needs no Spirit shield or other Spirit sensors and does not use Router Bridge. The UNO Q Qwiic socket uses `Wire1` and is **3.3 V only**; do not use the Spirit sketch on that port without changing its I²C bus configuration.

## Parts

- Arduino UNO Q, powered from its normal approved USB-C supply;
- empty UNO-compatible prototype shield **that does not short or backfeed any header** (or a breadboard/jumper leads);
- DS18B20 three-wire thermometer and **4.7 kΩ resistor** from DATA to 3.3 V (unless verified already on the module);
- Adafruit AS7343 14-channel multispectral breakout **#6477** with soldered header and jumper leads or compatible breakout-to-breadboard cable;
- DMM, short wires, optional oscilloscope or logic analyzer.

## Wiring contract

| Sensor | Sensor terminal | UNO Q header | Validation |
|---|---|---|---|
| DS18B20 | GND | GND | Confirm actual probe/breakout pin order from its supplier, **do not assume color order** |
| DS18B20 | VDD | **3V3** | Powered 3-wire mode, not parasite mode |
| DS18B20 | DQ/DATA | **D2** | **4.7 kΩ pull-up** to 3V3 on data line |
| Adafruit AS7343 #6477 | VIN | **3V3** | Adafruit breakout accepts 3–5 V VIN; not bare AS7343 IC |
| Adafruit AS7343 #6477 | GND | GND | Common ground |
| Adafruit AS7343 #6477 | SDA | **D20/SDA** | Default UNO Q Arduino `Wire` bus |
| Adafruit AS7343 #6477 | SCL | **D21/SCL** | Default UNO Q Arduino `Wire` bus |

### Layout (logical, not a physical connector illustration)

```text
 UNO Q + empty prototype shield
  3V3 -----+------------------- AS7343 VIN
           +--[ 4.7 kΩ ]--+
  D2 ---------------------+--- DS18B20 DQ
  3V3 ------------------------- DS18B20 VDD
  GND --------------------+---- DS18B20 GND
                          +---- AS7343 GND
  D20/SDA --------------------- AS7343 SDA
  D21/SCL --------------------- AS7343 SCL

  D3/D4 HX711: NOT CONNECTED   D7/D8 ultrasonic: NOT CONNECTED
  A4/A5: NOT USED by this prototype's `Wire` implementation
```

**DO NOT** stack the unmodified historical AVR Spirit 5-V PCB on the UNO Q. Its original HC-SR04 ECHO net was unshifted 5 V. Never apply external 5 V to the sensor logic on this provisional build. All wiring must be made with power **off**.

## Step-by-step procedure

1. Inspect UNO Q USB-C, 3V3 and GND connections and prototype board for shorts; measure continuity unpowered. Leave AS7343 and DS18B20 unplugged initially.
2. Verify Arduino UNO Q core and the four libraries. Compile and upload `UNO_Q_Spirit/UNO_Q_Spirit.ino` without sensors. No successful real-board compile has yet been recorded for this version.
3. From a shell on UNO Q's Qualcomm Debian: create/activate a Python venv with `arduino-router-bridge`; in the repo's `platforms/uno-q-spirit` directory run `python python/spirit_cli.py status`. It should report `mode: synthetic` after a fresh sketch start.
4. Power down; insert only the DS18B20 and 4.7 kΩ resistor, checking DATA idle voltage near **3.3 V** and absence of a 5-V pull-up. Power up again.
5. Power down; add the AS7343 four connections on D20/D21. On first power-up confirm the I²C lines idle near **3.3 V**, not 5 V; check the measured sensor address is 0x39 if running a separate I²C diagnostic.
6. Start the interactive bridge CLI (`python python/spirit_cli.py shell`), then enter:

```text
spirit> profile prototype
spirit> mode live
spirit> status
spirit> gain 6
spirit> status
```

7. Record `temp_c.state`, `temp_c.value`, `spectral.state`, and 18-channel `spectral.channels`; confirm **HX711 and ultrasonic state = DISABLED**, not erroneous readings or runaway counts. Allow ~2 seconds for a full AS7343 cycle and at least ~1 second for DS18B20 conversion before concluding a missing sensor.
8. Compare DS18B20 against a known thermometer under two stable temperatures. Test AS7343 with a steady lamp, shadow and different colors; sweep `gain 4`, `gain 6`, `gain 8` and reject `SATURATED` captures. These are **relative spectral counts**, not calibrated spectroradiometric watts/nm. Note integration timing and illumination geometry in the log.
9. With the system operating, briefly disconnect **one sensor at a time only after turning off power**; on restart, it should report MISSING/FAULT/TIMEOUT without stopping the other sensor. Record recovery after reconnect and power cycle. Do not hot-plug on a live breadboard for the initial experiment.
10. Acquire reproducible CSV from Debian:

```bash
python python/spirit_cli.py capture --count 30 --period 2 --output prototype_capture.csv
```

## Expected outcomes and limitations

| Condition | DS18B20 | AS7343 | HX711 | Ultrasonic |
|---|---|---|---|---|
| Synthetic startup | SYNTH | SYNTH | SYNTH | SYNTH |
| Live, both sensors present, prototype profile | OK | OK or SATURATED (gain dependent) | **DISABLED** | **DISABLED** |
| Live, DS18B20 absent | MISSING/FAULT | independent | DISABLED | DISABLED |
| Live, AS7343 absent | independent | MISSING or TIMEOUT | DISABLED | DISABLED |

Error states are design expectations; actual UNO Q silicon and peripheral timing are **not yet physically validated**. Current spectral driver's `readAllChannels()` can block for up to about one second while waiting for data; source-level C++ tests do **not** demonstrate hard-real-time boundedness. Test I²C bus faults, OneWire timing, sensor recovery and CLI responsiveness on hardware.

## Next stage after passing

1. Add HX711 DOUT **D3**, PD_SCK **D4** with an electrically verified **3.3 V breakout**, test tare/scale on reference weights.
2. Add verified 3.3 V ultrasonic sensor TRIG **D7**, ECHO **D8** (or level-shift 5 V ECHO) and measure jitter/timeouts.
3. Only then finalize the revised KiCad UNO Q Spirit PCB and decide whether to retain historic A4/A5 by explicitly using `Wire2` or reroute the spectral connection to D20/D21.

## Primary references

- User's `Nugget_2Wire_Sensor_Shield_KiCad_Autorouting_Programmers_Guide.pdf` (historic D2–D9, A4/A5 assignments and 5 V warnings)
- [Arduino UNO Q manual: I²C buses](https://docs.arduino.cc/tutorials/uno-q/user-manual/)
- [Arduino UNO Q full pinout](https://docs.arduino.cc/resources/pinouts/ABX00162-full-pinout.pdf)
- [Adafruit AS7343 breakout product #6477](https://www.adafruit.com/product/6477)
- [Adafruit AS7343 wiring](https://learn.adafruit.com/adafruit-as7343-14-channel-light-color-sensor-breakout/arduino)
- [Standalone direct-Qwiic test sketch](../examples/as7343-qwiic-test/as7343-qwiic-test.ino)
