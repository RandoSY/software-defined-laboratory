#pragma once
#include "Arduino.h"
class MockBridge {
public:
 bool begin(){return true;}
 template<typename Function> bool provide_safe(const char*,Function){return true;}
};
static MockBridge Bridge;
