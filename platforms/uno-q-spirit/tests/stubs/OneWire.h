#pragma once
// Absent-sensor fixture for the firmware simulation; no electrical timing or
// DS18B20 protocol behavior is emulated here.
#include "Arduino.h"
class OneWire {
public:
 explicit OneWire(int){}
 void reset_search(){}
 bool search(uint8_t*){return false;}
 static uint8_t crc8(const uint8_t*,uint8_t){return 0;}
 bool reset(){return false;}
 void select(const uint8_t*){}
 void write(uint8_t,int=0){}
 uint8_t read(){return 0;}
};
