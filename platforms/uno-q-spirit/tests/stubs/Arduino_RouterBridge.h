#pragma once
// Synchronous host stand-in: registration succeeds so firmware logic can be
// exercised without claiming an actual Router Bridge connection.
#include "Arduino.h"
class MockBridge {
public:
 bool begin(){return true;}
 template<typename Function> bool provide_safe(const char*,Function){return true;}
};
static MockBridge Bridge;
