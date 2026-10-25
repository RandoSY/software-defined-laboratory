# Standalone AS7343 test on UNO Q Qwiic

This is a small optical-sensor bring-up sketch for an Arduino UNO Q and an Adafruit AS7343 STEMMA QT/Qwiic breakout (#6477). It connects directly to the board's Qwiic socket with a STEMMA QT/Qwiic cable. It does **not** require the UNO Q Spirit shield, its prototype shield, a DS18B20, HX711, ultrasonic sensor, Python CLI, or Router Bridge.

The UNO Q's Qwiic socket is the separate 3.3 V I²C4 bus exposed as `Wire1`; the sketch passes `&Wire1` to the Adafruit driver. The default UNO header bus `Wire` on D20/D21 is not used.

## Hardware

- Arduino UNO Q and its normal approved power supply.
- Adafruit AS7343 breakout #6477.
- Four-wire STEMMA QT/Qwiic cable.

With board power off, connect the breakout to the UNO Q Qwiic socket. The connector provides 3.3 V, SDA, SCL, and GND. Use a compatible breakout with its onboard regulator/level shifting; do not connect a bare AS7343 IC. Power the board and sensor only through the intended board connector.

## Build and use

1. Install/update the Arduino UNO Q board package and the **Adafruit AS7343** library (including its Adafruit BusIO dependency).
2. Open `as7343-qwiic-test.ino` in Arduino IDE, select **Arduino UNO Q**, and compile/upload through the supported UNO Q workflow.
3. Open the Arduino serial monitor at **115200 baud**. The sketch first reports whether initialization succeeded, then emits CSV rows every two seconds with elapsed milliseconds, the driver's 18 readout slots, and analog/digital saturation flags.
4. Try a stable lamp, shade the sensor, and compare different colored light sources. Repeat with a lower or higher AS7343 gain in the sketch if readings are near zero or saturating.

The channel values are raw relative sensor counts, not calibrated spectral irradiance or a wavelength-resolved laboratory spectrometer measurement. This example verifies direct sensor communication and basic response only. It does not validate UNO Q Spirit firmware, Router Bridge, sensor accuracy, or electrical behavior of a Spirit shield.

## References

- [UNO Q manual: I²C and Qwiic](https://docs.arduino.cc/tutorials/uno-q/user-manual/)
- [Adafruit AS7343 STEMMA QT/Qwiic breakout](https://www.adafruit.com/product/6477)
- [Adafruit AS7343 Arduino guide](https://learn.adafruit.com/adafruit-as7343-14-channel-light-color-sensor-breakout/arduino)
