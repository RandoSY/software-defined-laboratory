/*
  SDL first-acceptance endpoint
  Arduino Uno + DS18B20 over USB serial

  Wiring (normal powered mode):
    DS18B20 VDD  -> 5V
    DS18B20 GND  -> GND
    DS18B20 DATA -> D2
    4.7 kOhm resistor from DATA to 5V

  The Multi-Function Shield may remain fitted; this baseline does not
  depend on shield peripherals. Change ONE_WIRE_BUS if D2 is unavailable
  on a particular shield/board combination.

  Required Arduino libraries:
    OneWire
    DallasTemperature

  Serial protocol:
    SDL,READY,DS18B20
    TEMP_C,23.625
    ERROR,SENSOR
*/

#include <OneWire.h>
#include <DallasTemperature.h>

constexpr uint8_t ONE_WIRE_BUS = 2;
constexpr unsigned long SAMPLE_INTERVAL_MS = 1000;

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
unsigned long lastSample = 0;

void setup() {
  Serial.begin(115200);
  sensors.begin();
  delay(250);
  Serial.println(F("SDL,READY,DS18B20"));
}

void loop() {
  const unsigned long now = millis();
  if (now - lastSample < SAMPLE_INTERVAL_MS) {
    return;
  }
  lastSample = now;

  sensors.requestTemperatures();
  const float tempC = sensors.getTempCByIndex(0);

  if (tempC == DEVICE_DISCONNECTED_C || tempC < -55.0f || tempC > 125.0f) {
    Serial.println(F("ERROR,SENSOR"));
    return;
  }

  Serial.print(F("TEMP_C,"));
  Serial.println(tempC, 3);
}
