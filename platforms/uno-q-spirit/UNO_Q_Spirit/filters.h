#pragma once
#include <stdint.h>
#include <math.h>

namespace spirit {
// Welford's online algorithm: constant memory and numerically stable for long
// streams. stddev() below reports the sample standard deviation (n - 1).
struct RunningStat {
  unsigned n = 0;
  double mean = 0.0;
  double m2 = 0.0;
  void reset() { n = 0; mean = 0; m2 = 0; }
  bool add(double value) {
    if (!isfinite(value)) return false;
    ++n;
    const double delta = value - mean;
    mean += delta / n;
    m2 += delta * (value - mean);
    return true;
  }
  double stddev() const { return n > 1 ? sqrt(m2 / (n - 1)) : 0.0; }
};

// Convert the round-trip ECHO pulse width to one-way sensor distance in cm.
inline double echoCm(uint32_t microseconds, double temperatureC) {
  if (microseconds == 0 || microseconds > 30000 ||
      !isfinite(temperatureC) || temperatureC < -40 || temperatureC > 85) return NAN;
  // speed of sound in dry air ~331.3 + 0.606*T [m/s]
  return microseconds * (331.3 + 0.606 * temperatureC) / 20000.0;
}

// Sign-extend the HX711's 24-bit two's-complement ADC word into int32_t.
inline int32_t signed24(uint32_t raw) {
  raw &= 0xFFFFFFUL;
  return (raw & 0x800000UL) ? static_cast<int32_t>(raw | 0xFF000000UL) : static_cast<int32_t>(raw);
}

// -127 C is rejected by range; +85 C is the DS18B20 power-up/error sentinel.
inline bool plausibleTemperature(double t) { return isfinite(t) && t >= -55.0 && t <= 125.0 && t != 85.0; }
// Shared lower/upper bounds for the MCU interval command, in milliseconds.
inline bool validInterval(int ms) { return ms >= 100 && ms <= 10000; }
}
