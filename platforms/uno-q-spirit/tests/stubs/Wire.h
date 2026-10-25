#pragma once
// Minimal default-Wire stand-in used by host sketch tests. It reports no I2C
// acknowledgement; the standalone Qwiic sketch is built against the real core.
#include "Arduino.h"
struct TwoWire {
 void begin(){};
 void beginTransmission(int){};
 int endTransmission(){return 4;}
};
static TwoWire Wire;
