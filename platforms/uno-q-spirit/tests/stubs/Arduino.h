#pragma once
#include <cstdint>
#include <cmath>
#include <cstring>
#include <string>
#include <utility>
using uint8_t = std::uint8_t;
using uint32_t = std::uint32_t;
constexpr int OUTPUT=1, INPUT=0, INPUT_PULLUP=2, LOW=0, HIGH=1;
class String {
  std::string v;
public:
  String()=default;
  String(const char* s):v(s?s:""){}
  String(const std::string& s):v(s){}
  String(bool b):v(b?"1":"0"){}
  String(int x):v(std::to_string(x)){}
  String(unsigned x):v(std::to_string(x)){}
  String(unsigned long x):v(std::to_string(x)){}
  String(long x):v(std::to_string(x)){}
  String(float f,int precision=2):v(std::to_string(f).substr(0,std::to_string(f).find('.')+1+precision)){}
  String(double f,int precision=2):v(std::to_string(f).substr(0,std::to_string(f).find('.')+1+precision)){}
  size_t length() const {return v.size();}
  void trim() {auto n=v.find_first_not_of(" \r\n\t");if(n==std::string::npos){v.clear();return;}auto last=v.find_last_not_of(" \r\n\t");v=v.substr(n,last-n+1);}
  String substring(size_t n) const {return String(v.substr(n));}
  bool startsWith(const char* s) const {return v.rfind(s,0)==0;}
  int toInt() const {try{return std::stoi(v);}catch(...){return 0;}}
  float toFloat() const {try{return std::stof(v);}catch(...){return 0;}}
  char operator[](size_t i) const {return v[i];}
  bool operator==(const char* s) const {return v==s;}
  bool operator!=(const char* s) const {return v!=s;}
  String& operator+=(const String& s){v+=s.v;return *this;}
  String& operator+=(const char* s){v+=s;return *this;}
  friend String operator+(const String& a,const String& b){return String(a.v+b.v);}
  friend String operator+(const char* a,const String& b){return String(std::string(a)+b.v);}
  const std::string& str() const {return v;}
};
inline bool isDigit(char c){return c>='0'&&c<='9';}
inline unsigned long &fakeTime(){static unsigned long n=0;return n;}
inline unsigned long millis(){return fakeTime();}
inline void delayMicroseconds(unsigned){}
inline void pinMode(int,int){}
inline int digitalRead(int pin){return (pin==3||pin==8)?HIGH:HIGH;}
inline void digitalWrite(int,int){}
inline unsigned long pulseIn(int,int,unsigned long){return 0;}
inline void noInterrupts(){}
inline void interrupts(){}
