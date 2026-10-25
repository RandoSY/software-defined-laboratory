// SPDX-License-Identifier: MIT
// Standalone UNO Q Qwiic/STEMMA QT test for Adafruit AS7343 breakout #6477.
// This sketch does not use the UNO Q Spirit shield, Router Bridge, or other sensors.
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_AS7343.h>

Adafruit_AS7343 as7343;
uint16_t channels[18] = {0};
uint32_t lastSampleMs = 0;
bool sensorReady = false;

void setup() {
  Serial.begin(115200);
  const uint32_t waitStarted = millis();
  while (!Serial && millis() - waitStarted < 5000) {
    delay(10);
  }

  // On UNO Q, the physical Qwiic connector is I2C4 and is Arduino Wire1.
  Wire1.begin();

  Serial.println("UNO Q standalone AS7343 Qwiic test");
  Serial.println("sensor_address=0x39 bus=Wire1 connector=Qwiic/STEMMA_QT");

  sensorReady = as7343.begin(AS7343_I2CADDR_DEFAULT, &Wire1);
  if (sensorReady) {
    sensorReady = as7343.setSMUXMode(AS7343_SMUX_18CH)
      && as7343.setGain(AS7343_GAIN_64X)
      && as7343.setATIME(29)
      && as7343.setASTEP(599);
  }

  if (!sensorReady) {
    Serial.println("ERROR,AS7343_NOT_FOUND_OR_INIT_FAILED");
    Serial.println("Check the Qwiic cable, 3V3 power, GND, and sensor breakout.");
    return;
  }

  Serial.println("elapsed_ms,c0,c1,c2,c3,c4,c5,c6,c7,c8,c9,c10,c11,c12,c13,c14,c15,c16,c17,analog_saturated,digital_saturated");
}

void loop() {
  if (!sensorReady) {
    delay(1000);
    return;
  }

  const uint32_t now = millis();
  if (now - lastSampleMs < 2000) {
    delay(10);
    return;
  }
  lastSampleMs = now;

  if (!as7343.readAllChannels(channels)) {
    Serial.print(now);
    Serial.println(",ERROR,READ_FAILED");
    return;
  }

  Serial.print(now);
  for (uint8_t i = 0; i < 18; ++i) {
    Serial.print(',');
    Serial.print(channels[i]);
  }
  Serial.print(',');
  Serial.print(as7343.isAnalogSaturated() ? 1 : 0);
  Serial.print(',');
  Serial.println(as7343.isDigitalSaturated() ? 1 : 0);
}
