#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include "../../UNO_Q_Spirit/filters.h"
int main(){
  // Edge values matter here: the sketch converts two's-complement 24-bit HX711
  // samples and must reject impossible distance/temperature inputs as NaN.
  assert(spirit::signed24(0)==0);
  assert(spirit::signed24(0x7fffff)==8388607);
  assert(spirit::signed24(0x800000)==-8388608);
  assert(spirit::signed24(0xffffff)==-1);
  assert(std::isnan(spirit::echoCm(0,20)));
  assert(std::isnan(spirit::echoCm(30001,20)));
  assert(std::isnan(spirit::echoCm(1000,INFINITY)));
  assert(std::abs(spirit::echoCm(1000,20)-17.171)<0.01);
  assert(spirit::plausibleTemperature(22));
  assert(!spirit::plausibleTemperature(85));
  assert(!spirit::plausibleTemperature(-127));
  assert(spirit::validInterval(100));
  assert(spirit::validInterval(10000));
  assert(!spirit::validInterval(99));
  assert(!spirit::validInterval(10001));
  spirit::RunningStat stats;
  // Online sample variance is reviewed against a small hand-checkable series.
  assert(!stats.add(NAN));
  assert(stats.add(2)); assert(stats.add(4)); assert(stats.add(6));
  assert(stats.n==3 && stats.mean==4);
  assert(std::abs(stats.stddev()-2)<1e-8);
  stats.reset(); assert(stats.n==0);
  std::cout << "PASS: 19 C++ assertions\n";
}
