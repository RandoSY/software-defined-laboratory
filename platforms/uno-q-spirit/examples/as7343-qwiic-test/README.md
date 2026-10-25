# Standalone AS7343 test on UNO Q

This is a small optical-sensor bring-up sketch for an Arduino UNO Q and an Adafruit AS7343 breakout (#6477). It automatically tries the board's Qwiic socket with a STEMMA QT/Qwiic cable first, then falls back to four jumper wires on the standard D20/D21 I²C header. It does **not** require the UNO Q Spirit shield, its prototype shield, a DS18B20, HX711, ultrasonic sensor, Python CLI, or Router Bridge.

The UNO Q's Qwiic socket is the separate 3.3 V I²C4 bus exposed as `Wire1`; the regular D20/D21 header is `Wire`. The sketch initializes both buses and looks for the AS7343 on Qwiic first, then on D20/D21. Connect the breakout to either one; the sketch reports which bus it found.

## Hardware

- Arduino UNO Q and its normal approved power supply.
- Adafruit AS7343 breakout #6477.
- Four-wire STEMMA QT/Qwiic cable.

For the no-Qwiic option, use four jumper leads and connect the breakout to the standard header as shown below instead of using the STEMMA cable. The sketch detects this connection automatically.

| Breakout | UNO Q header when using D20/D21 header |
|---|---|
| VIN | 3V3 |
| GND | GND |
| SDA | D20 / SDA |
| SCL | D21 / SCL |

With board power off, connect the breakout to either the Qwiic socket or the header pins in the table. The Qwiic connector provides 3.3 V, SDA, SCL, and GND; use 3V3 for header wiring. Use a compatible breakout with its onboard regulator/level shifting; do not connect a bare AS7343 IC. Do not connect both buses at once during this smoke test.

## Build and use

1. Install/update the Arduino UNO Q board package and the **Adafruit AS7343** library (including its Adafruit BusIO dependency).
2. Connect the sensor to either the Qwiic socket or the D20/D21 header with board power off. The sketch tries Qwiic first and automatically falls back to the header.
3. Open `as7343-qwiic-test.ino` in Arduino IDE, select **Arduino UNO Q**, and compile/upload through the supported UNO Q workflow.
4. Open the Arduino serial monitor at **115200 baud**. The sketch first reports whether initialization succeeded, then emits CSV rows every two seconds with elapsed milliseconds, the driver's 18 readout slots, and analog/digital saturation flags.
5. Try a stable lamp, shade the sensor, and compare different colored light sources. Repeat with a lower or higher AS7343 gain in the sketch if readings are near zero or saturating.

The channel values are raw relative sensor counts, not calibrated spectral irradiance or a wavelength-resolved laboratory spectrometer measurement. This example verifies direct sensor communication and basic response only. It does not validate UNO Q Spirit firmware, Router Bridge, sensor accuracy, or electrical behavior of a Spirit shield.

## References

- [UNO Q manual: I²C and Qwiic](https://docs.arduino.cc/tutorials/uno-q/user-manual/)
- [Adafruit AS7343 STEMMA QT/Qwiic breakout](https://www.adafruit.com/product/6477)
- [Adafruit AS7343 Arduino guide](https://learn.adafruit.com/adafruit-as7343-14-channel-light-color-sensor-breakout/arduino)
