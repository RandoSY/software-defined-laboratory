# UNO Q Spirit — two-sensor prototype-shield quickstart

**Procedure:** UQS-TP-01 · **Date:** 2026-10-25 · **Status:** engineering prototype, hardware validation pending

## Mission

There is **no need to design or manufacture a new Spirit board first**. Start with an empty UNO-style prototype shield (or a solderless breadboard and leads), the **DS18B20 three-wire thermometer**, and the **Adafruit AS7343 multispectral breakout #6477**. Leave HX711, ultrasonic, START/TARE switches and active buzzer disconnected.

The firmware boots in **synthetic mode**. The new interactive Bridge command `profile prototype` keeps **only DS18B20 and AS7343 acquisition active in live mode**. It reports `DISABLED` for HX711 and ultrasonic instead of polling absent hardware. The `profile all` command restores acquisition on all four sensor families.

## Critical correction to the old AVR Spirit I²C assumptions

The Nugget/AVR Spirit historical v0.2x documentation used **A4 (SDA) and A5 (SCL)** on the original **5 V Arduino UNO**. The **UNO Q** official Arduino manual specifies the default `Wire` object as **D20 (SDA, PB11) and D21 (SCL, PB10)**, not A4/A5. This firmware uses `Wire.begin()` and `as7343.begin(0x39, &Wire)`. **Wire the AS7343 to D20/D21.** The historical A4/A5 pads (PC1/PC0, a separate I²C-capable bus) will not operate with this default `Wire` configuration.

A newer UNO Q core has `Wire2` support for A4/A5, but changing to that bus requires checking the installed core, altering the source, and repeating tests. The UNO Q built-in **Qwiic** socket uses `Wire1`, also requiring a source change. Both are future options; the present four-wire prototype uses D20/D21 as written.

## Parts

- UNO Q with an approved USB-C 5 V/3 A power arrangement.
- Empty electrically compatible UNO prototype shield or solderless breadboard.
- DS18B20 in **powered three-wire mode** and a 4.7 kΩ DATA-to-3.3 V resistor (unless already verified on the breakout).
- Adafruit AS7343 breakout **#6477** (not a bare AS7343 IC), with soldered connector/header.
- Jumper leads, voltmeter and optionally a logic analyzer.

## Wiring

| Component | Terminal | UNO Q header | Note |
|---|---|---|---|
| DS18B20 | GND | GND | Check actual module/probe pin order, not cable color |
| DS18B20 | VDD | 3V3 | Never use 5 V for this first setup |
| DS18B20 | DATA/DQ | **D2** | Add **4.7 kΩ pull-up from DATA to 3V3** |
| Adafruit AS7343 | VIN | 3V3 | Adafruit breakout has regulator/level translation |
| Adafruit AS7343 | GND | GND | Shared ground |
| Adafruit AS7343 | SDA | **D20 (SDA)** | Default `Wire` |
| Adafruit AS7343 | SCL | **D21 (SCL)** | Default `Wire` |

Logical wiring, not a scale mechanical drawing:

```text
 UNO Q 3V3 ---+--- DS18B20 VDD
              +--- AS7343 VIN
              +---[4.7k]---+
 UNO Q D2 -----------------+--- DS18B20 DATA/DQ
 UNO Q GND ---+---------------- DS18B20 GND
              +---------------- AS7343 GND
 UNO Q D20/SDA -------------- AS7343 SDA
 UNO Q D21/SCL -------------- AS7343 SCL

 D3,D4: HX711 DISCONNECTED     D7,D8: ultrasonic DISCONNECTED
 A4,A5: historical I²C pins, NOT used by this sketch's Wire bus
```

**Do not use the original unmodified 5 V Spirit PCB as the prototype shield.** Its HC-SR04 ECHO connection was deliberately unshifted and may put 5 V on an STM32 input. Keep screw-terminal/external sensor power disconnected. Power down before inserting or moving wires.

## Bring-up sequence

1. Verify the empty shield has **no shorts** among GND, 3V3, and 5 V and no hidden 5 V pull-ups. Attach no devices yet.
2. Build/upload `UNO_Q_Spirit/UNO_Q_Spirit.ino` using Arduino UNO Q board support and installed **OneWire**, **Adafruit AS7343**, **Adafruit BusIO**, and **Arduino_RouterBridge** libraries. The real UNO Q compile/upload is a *pending* acceptance gate; host-stub compilation alone is insufficient.
3. On the Qualcomm Debian terminal, activate the Python environment with `arduino-router-bridge`, then run `python python/spirit_cli.py status` inside `platforms/uno-q-spirit`. Initial `mode` should be `synthetic`.
4. Power down; connect the **DS18B20** and resistor. Check its DATA idle pull-up is around **3.3 V**. Power up and check no brownout.
5. Power down; connect the **AS7343**. Confirm idle SDA/SCL are **approximately 3.3 V**, not 5 V. Power up. The Adafruit sensor address should be **0x39**.
6. Open `python python/spirit_cli.py shell` and enter:

```text
spirit> profile prototype
spirit> mode live
spirit> status
spirit> gain 6
spirit> status
```

7. Allow at least one full DS18B20 conversion (~750 ms at 12-bit) and an AS7343 scan (configured every 2 s) before judging readiness. Expected: `temp_c.state` is `OK`; `spectral.state` is `OK` or `SATURATED`; **`hx711_counts.state` and `distance_cm.state` are `DISABLED`**.
8. Check temperature against a reference. Take repeated AS7343 samples at fixed illumination/geometry and use `gain 4` / `gain 6` / `gain 8` to evaluate sensitivity versus saturation. The array contains **18 hardware readout slots** (including repeated clear readings), not 18 independent spectral wavelengths, and counts are not calibrated radiometric units.
9. Capture 30 observations at 2-second intervals:

```bash
python python/spirit_cli.py capture --count 30 --period 2 --output prototype_capture.csv
```

10. Test missing-sensor fault handling **by powering down before each disconnection and reconnection**. After restart, the remaining sensor should still function and the absent one should show a fault/missing state, not crash acquisition.

## Acceptance criteria

| Scenario | DS18B20 | AS7343 | HX711 | Ultrasonic |
|---|---|---|---|---|
| Fresh startup (synthetic) | SYNTH | SYNTH | SYNTH | SYNTH |
| Live + prototype profile, both installed | OK | OK / SATURATED | DISABLED | DISABLED |
| DS18B20 unplugged at power-off | MISSING / FAULT | Independent | DISABLED | DISABLED |
| AS7343 unplugged at power-off | Independent | MISSING / TIMEOUT | DISABLED | DISABLED |

Record measured voltages, library/core versions, run duration, retries, worst observed timing, CSV, sensor disconnections and diagnostic status. This release **has not yet passed physical measurement acceptance**. OneWire timing under Zephyr and Adafruit AS7343's potentially blocking I²C operations must be examined on the actual board.

## Expansion path

After the two-sensor test passes: connect a verified 3.3 V HX711 breakout on D3/D4, then a verified 3.3 V ultrasonic module on D7/D8 or a properly translated 5 V ECHO path. Use `profile all` only after the additional connections pass electrical checks.

**Sources:** [UNO Q Arduino user manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/); [UNO Q pinout](https://docs.arduino.cc/resources/pinouts/ABX00162-full-pinout.pdf); [Adafruit AS7343 breakout](https://www.adafruit.com/product/6477); user's historic *Nugget 2-Wire Sensor Shield KiCad Autorouting and Programmer's Guide*.
