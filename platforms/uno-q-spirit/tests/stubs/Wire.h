#pragma once
#include "Arduino.h"
struct TwoWire {
 void begin(){};
 void beginTransmission(int){};
 int endTransmission(){return 4;}
};
static TwoWire Wire;
