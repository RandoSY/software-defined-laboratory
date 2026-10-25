#pragma once
// Minimal host stub. Initialization/readout intentionally fail to model an
// absent sensor; success cases require the real board/library example build.
#include "Wire.h"
enum as7343_gain_t { AS7343_GAIN_64X=6 };
enum as7343_smux_mode_t { AS7343_SMUX_18CH=3 };
class Adafruit_AS7343 {
public:
 bool begin(uint8_t,TwoWire*){return false;}
 bool setSMUXMode(as7343_smux_mode_t){return true;}
 bool setGain(as7343_gain_t){return true;}
 bool setATIME(uint8_t){return true;}
 bool setASTEP(uint16_t){return true;}
 bool readAllChannels(uint16_t*){return false;}
 bool isAnalogSaturated(){return false;}
 bool isDigitalSaturated(){return false;}
};
