// SPDX-License-Identifier: MIT
// Standalone UNO Q Qwiic/STEMMA QT test for Adafruit AS7343 breakout #6477.
// This sketch does not use the UNO Q Spirit shield, Router Bridge, or other sensors.
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_AS7343.h>

Adafruit_AS7343 as7343;
TwoWire *sensorBus = nullptr;
const char *sensorBusName = "unavailable";
// Adafruit's 18-slot SMUX readout is a driver layout, not 18 calibrated
// wavelength bins; treat these values as relative raw counts.
uint16_t channels[18] = {0};
uint32_t lastSampleMs = 0;
bool sensorReady = false;

bool beginOnBus(TwoWire &bus) {
  // Avoid running the driver's initialization/reset sequence on an empty bus.
  bus.beginTransmission(AS7343_I2CADDR_DEFAULT);
  if (bus.endTransmission() != 0) return false;
  if (!as7343.begin(AS7343_I2CADDR_DEFAULT, &bus)) return false;

  const bool configured = as7343.setSMUXMode(AS7343_SMUX_18CH)
    && as7343.setGain(AS7343_GAIN_64X)
    && as7343.setATIME(29)
    && as7343.setASTEP(599);
  if (!configured) return false;
  sensorBus = &bus;
  return true;
}

void setup() {
  Serial.begin(115200);
  const uint32_t waitStarted = millis();
  while (!Serial && millis() - waitStarted < 5000) {
    delay(10);
  }

  // Try Qwiic first, then the regular header. This makes the connector choice
  // physical and automatic; no source edit is needed when changing the wiring.
  Wire1.begin();
  if (beginOnBus(Wire1)) {
    sensorBusName = "Wire1 / Qwiic-STEMMA QT";
  } else {
    Wire.begin();
    if (beginOnBus(Wire)) sensorBusName = "Wire / D20-D21";
  }

  sensorReady = sensorBus != nullptr;
  Serial.println("UNO Q standalone AS7343 test");
  Serial.print("sensor_address=0x39 bus=");
  Serial.println(sensorBusName);

  if (!sensorReady) {
    Serial.println("ERROR,AS7343_NOT_FOUND_OR_INIT_FAILED");
    Serial.println("Check the Qwiic/header connection, 3V3 power, GND, and breakout.");
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

  // The library waits for its integration to finish here; timing is suitable
  // for a bench smoke test, not a hard-real-time acquisition loop.
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
