// UNO Q Spirit v0.1.0: defensive mixed-sensor lab demonstrator.
// Target Arduino UNO Q STM32U585 (Arduino's Zephyr core); start SYNTHETIC.
// D2-D9 from historical Nugget 2-Wire Sensor Shield v0.2x.
// UNO Q Wire uses D20=SDA/D21=SCL, unlike historical A4/A5 I2C.
// DO NOT MATE A 5V AVR SPIRIT PCB TO UNO Q without electrical adaptation.
#include <Arduino.h>
#include <Wire.h>
#include <OneWire.h>
#include <Adafruit_AS7343.h>
#include <Arduino_RouterBridge.h>
#include <zephyr/kernel.h>
#include "filters.h"

constexpr uint8_t PIN_DS18=2, PIN_HX_DOUT=3, PIN_HX_SCK=4;
constexpr uint8_t PIN_START=5, PIN_TARE=6, PIN_TRIG=7, PIN_ECHO=8, PIN_BUZZER=9;
constexpr uint8_t AS7343_ADDRESS=0x39;
constexpr uint32_t HX_READY_PERIOD_MS=125, US_PERIOD_MS=300, TEMP_PERIOD_MS=1000;
constexpr uint32_t SPEC_PERIOD_MS=2000, DEVICE_RETRY_MS=5000;
constexpr uint32_t ECHO_TIMEOUT_US=30000;

OneWire oneWire(PIN_DS18);
Adafruit_AS7343 as7343;
bool live=false, acquiring=true, spectrumFound=false, dsFound=false;
bool prototypeProfile=false; // Live: DS18B20 + AS7343 only; other acquisition disabled.
volatile bool bridgeOk=false;
bool temperatureRequested=false, haveTemperature=false;
uint8_t dsAddr[8]={0};
uint32_t lastHX=0, lastUS=0, lastTemp=0, lastSpec=0, lastRetry=0;
uint32_t tempStarted=0, lastClock=0, lastTick=0, totalTicks=0;
uint32_t missedTicks=0;
uint32_t uptimeStart=0;
uint32_t syntheticCounter=0;
uint32_t lastHXok=0;
float tempC=22.0f, distanceCm=50.0f, hxGrams=NAN;
int32_t hxRaw=0, hxOffset=0;
float hxScale=0.0f; // raw counts per gram; 0 means NOT CALIBRATED
uint16_t spectrum[18]={0};
uint8_t spectralGain=6; // AS7343_GAIN_64X
const char *tempState="DISABLED", *hxState="DISABLED", *usState="DISABLED", *specState="DISABLED";
spirit::RunningStat hxStats, usStats, jitterStats;
uint32_t successTemp=0, successHX=0, successUS=0, successSpec=0;
uint32_t errorTemp=0, errorHX=0, errorUS=0, errorSpec=0;
uint32_t systemIntervalMs=1000;
uint32_t lastHeartbeat=0;
bool startLast=false, tareLast=false;
uint32_t lastStartEdge=0, lastTareEdge=0;

void resetStreams() {
  hxStats.reset(); usStats.reset(); jitterStats.reset();
  successTemp=successHX=successUS=successSpec=0;
  errorTemp=errorHX=errorUS=errorSpec=0;
  haveTemperature=false; temperatureRequested=false;
  hxScale=0; hxGrams=NAN; hxOffset=0; // NEVER carry calibration across modes
}

void setSyntheticStates() {
  tempState=hxState=usState=specState="SYNTH";
  dsFound=false; spectrumFound=false;
}

bool findDS18() {
  oneWire.reset_search();
  uint8_t address[8];
  // Bounded to 8 discovered ROMs and CRC-checked for DS18B20 family 0x28.
  for (uint8_t i=0; i<8 && oneWire.search(address); i++) {
    if (address[0]==0x28 && OneWire::crc8(address,7)==address[7]) {
      memcpy(dsAddr,address,8); return true;
    }
  }
  return false;
}

void probeDevices() {
  if (!live) return;
  if (!dsFound) {
    dsFound=findDS18();
    tempState=dsFound?"WARMUP":"MISSING";
    if (!dsFound) errorTemp++;
  }
  if (!spectrumFound) {
    Wire.beginTransmission(AS7343_ADDRESS);
    if (Wire.endTransmission()==0 && as7343.begin(AS7343_ADDRESS, &Wire)) {
      spectrumFound=as7343.setSMUXMode(AS7343_SMUX_18CH)
        && as7343.setGain(static_cast<as7343_gain_t>(spectralGain))
        && as7343.setATIME(29) && as7343.setASTEP(599);
    } else spectrumFound=false;
    specState=spectrumFound?"WARMUP":"MISSING";
    if (!spectrumFound) errorSpec++;
  }
}

void setMode(bool enabled) {
  live=enabled; resetStreams();
  digitalWrite(PIN_TRIG,LOW); digitalWrite(PIN_HX_SCK,LOW);
  digitalWrite(PIN_BUZZER,LOW);
  if (live) {
    dsFound=false; spectrumFound=false;
    tempState=specState="WARMUP";
    hxState=usState=prototypeProfile?"DISABLED":"WARMUP";
    lastRetry=millis()-DEVICE_RETRY_MS;
    // All device probes and missing sensor handling remain bounded except
    // upstream I2C driver timeout; Wire.setWireTimeout is core dependent.
  } else {setSyntheticStates();}
}

// HX711 raw 24-bit read, no library's potentially infinite wait_ready() loop.
// One interrupt-masked transfer prevents >60us clock-high stretching.
// IMPORTANT: Validate timing on actual Zephyr board with a logic analyzer.
bool readHX711(int32_t &out) {
  if (digitalRead(PIN_HX_DOUT)!=LOW) return false;
  uint32_t raw=0;
  noInterrupts();
  for (uint8_t i=0; i<24; ++i) {
    digitalWrite(PIN_HX_SCK,HIGH);
    delayMicroseconds(1);
    raw=(raw<<1)|(digitalRead(PIN_HX_DOUT)==HIGH?1UL:0UL);
    digitalWrite(PIN_HX_SCK,LOW);
    delayMicroseconds(1);
  }
  digitalWrite(PIN_HX_SCK,HIGH); // 25th pulse selects Channel A gain 128
  delayMicroseconds(1);
  digitalWrite(PIN_HX_SCK,LOW);
  interrupts();
  out=spirit::signed24(raw);
  return true;
}

void updateHX(uint32_t now) {
  if (digitalRead(PIN_HX_DOUT)!=LOW) {
    if (now-lastHXok>1500) {hxState="TIMEOUT"; ++errorHX; lastHXok=now;}
    return;
  }
  int32_t value;
  if (!readHX711(value)) {hxState="FAULT";errorHX++;return;}
  hxRaw=value;
  hxState="OK"; lastHXok=now;
  successHX++; hxStats.add(static_cast<double>(value));
  hxGrams=(hxScale!=0.0f) ? (value-hxOffset)/hxScale : NAN;
}

void beginTemperature(uint32_t now) {
  if (!dsFound) {tempState="MISSING"; return;}
  if (!oneWire.reset()) {tempState="MISSING";dsFound=false;errorTemp++;return;}
  oneWire.select(dsAddr); oneWire.write(0x44,0); // powered 3-wire mode ONLY
  temperatureRequested=true; tempStarted=now; tempState="WARMUP";
}

void finishTemperature(uint32_t now) {
  if (!temperatureRequested || now-tempStarted<750) return;
  temperatureRequested=false;
  if (!oneWire.reset()) { tempState="MISSING";dsFound=false;errorTemp++;return; }
  oneWire.select(dsAddr);oneWire.write(0xBE);
  uint8_t data[9]; for (uint8_t i=0;i<9;i++)data[i]=oneWire.read();
  if (OneWire::crc8(data,8)!=data[8]) {tempState="FAULT";errorTemp++;return;}
  int16_t raw=static_cast<int16_t>(static_cast<uint16_t>(data[0]) | (static_cast<uint16_t>(data[1])<<8));
  const float value=raw/16.0f;
  if (!spirit::plausibleTemperature(value)) {tempState="FAULT";errorTemp++;return;}
  tempC=value;haveTemperature=true;tempState="OK";successTemp++;
}

void updateUS() {
  digitalWrite(PIN_TRIG,LOW); delayMicroseconds(3);
  digitalWrite(PIN_TRIG,HIGH);delayMicroseconds(10);digitalWrite(PIN_TRIG,LOW);
  const uint32_t duration=pulseIn(PIN_ECHO,HIGH,ECHO_TIMEOUT_US);
  const double cm=spirit::echoCm(duration,haveTemperature ? tempC : 20.0);
  if (!isfinite(cm) || cm<2.0 || cm>400.0) {usState=duration?"FAULT":"TIMEOUT";errorUS++;return;}
  distanceCm=static_cast<float>(cm);usState="OK";successUS++;usStats.add(cm);
}

void updateSpectral() {
  if (!spectrumFound) {specState="MISSING";return;}
  uint16_t buf[18]={0};
  // Upstream Adafruit readAllChannels has a <=1000 ms data-ready wait;
  // the bus driver itself must be verified for I2C fault timeouts.
  if (!as7343.readAllChannels(buf)) {specState="TIMEOUT";errorSpec++;spectrumFound=false;return;}
  bool saturation=as7343.isAnalogSaturated() || as7343.isDigitalSaturated();
  memcpy(spectrum,buf,sizeof(spectrum));
  specState=saturation?"SATURATED":"OK";
  successSpec++;
}

void synthTick(uint32_t now) {
  const float phase=(now-uptimeStart)*0.001f;
  tempC=22.0f+2.5f*sinf(phase*0.12f);
  distanceCm=50.0f+10.0f*sinf(phase*0.38f);
  hxRaw=82500+static_cast<int32_t>(700*sinf(phase*0.8f));
  hxGrams=static_cast<float>(hxRaw-hxOffset)/1000.0f;
  hxStats.add(hxRaw); usStats.add(distanceCm);
  const float spectralBase=23000.0f+2000.0f*sinf(phase*0.15f);
  for (uint8_t i=0;i<18;i++)spectrum[i]=static_cast<uint16_t>(spectralBase*(0.22f+0.03f*i)*(1.0f+0.08f*sinf(phase*0.6f+i)));
  tempState=hxState=usState=specState="SYNTH";
  ++successTemp;++successHX;++successUS;++successSpec;
  ++syntheticCounter;
}

String quote(const char* s) {return String("\"")+s+"\"";}
String sensorJSON(const char* state, double value, uint32_t passed, uint32_t failed) {
  String out="{\"state\":"+quote(state)+",\"value\":";
  if ((strcmp(state,"OK")==0 || strcmp(state,"SYNTH")==0) && isfinite(value)) out+=String(value,3); else out+="null";
  out+=",\"ok_count\":"+String(passed)+",\"error_count\":"+String(failed)+"}";
  return out;
}
String statusJSON() {
  String s="{\"schema\":1,\"mode\":"+quote(live?"live":"synthetic")+
    ",\"run\":"+String(acquiring?"true":"false")+
    ",\"uptime_ms\":"+String(millis()-uptimeStart)+
    ",\"profile\":"+quote(prototypeProfile?"prototype":"all")+
    ",\"interval_ms\":"+String(systemIntervalMs)+
    ",\"bridge_ok\":"+String(bridgeOk?"true":"false")+
    ",\"temp_c\":"+sensorJSON(tempState,tempC,successTemp,errorTemp)+
    ",\"hx711_counts\":"+sensorJSON(hxState,hxRaw,successHX,errorHX)+
    ",\"hx711_grams\":";
  s+=((strcmp(hxState,"OK")==0 || strcmp(hxState,"SYNTH")==0) && isfinite(hxGrams))?String(hxGrams,3):String("null");
  s+=",\"hx711_calibrated\":"+String(live && hxScale!=0.0f?"true":"false")+
    ",\"distance_cm\":"+sensorJSON(usState,distanceCm,successUS,errorUS)+
    ",\"spectral\":{\"state\":"+quote(specState)+
    ",\"gain_code\":"+String(spectralGain)+
    ",\"ok_count\":"+String(successSpec)+
    ",\"error_count\":"+String(errorSpec)+
    ",\"channels\":[";
  for (uint8_t i=0;i<18;i++){if(i)s+=",";s+=String(spectrum[i]);}
  s+="]},\"jitter_std_ms\":"+String(jitterStats.stddev(),3)+
    ",\"hx_counts_stddev\":"+String(hxStats.stddev(),3)+
    ",\"ultrasonic_cm_stddev\":"+String(usStats.stddev(),3)+
    ",\"loop_ticks\":"+String(totalTicks)+"}";
  return s;
}

String command(String cmd) {
  cmd.trim();
  if(cmd=="help")return "{\"ok\":true,\"commands\":[\"mode synthetic\",\"mode live\",\"profile prototype\",\"profile all\",\"start\",\"stop\",\"tare\",\"gain 0..12\",\"interval 100..10000\",\"reset-stats\",\"cal grams <known mass>\"]}";
  if(cmd=="mode synthetic") {setMode(false);return "{\"ok\":true,\"mode\":\"synthetic\"}";}
  if(cmd=="mode live") {setMode(true);return "{\"ok\":true,\"mode\":\"live\"}";}
  if(cmd=="profile prototype" || cmd=="profile all") {
    prototypeProfile=(cmd=="profile prototype");
    setMode(live); // clear stale data on configuration change
    return prototypeProfile?"{\"ok\":true,\"profile\":\"prototype\"}":"{\"ok\":true,\"profile\":\"all\"}";
  }
  if(cmd=="start") {acquiring=true;return "{\"ok\":true}";}
  if(cmd=="stop") {acquiring=false;digitalWrite(PIN_BUZZER,LOW);return "{\"ok\":true}";}
  if(cmd=="reset-stats") {resetStreams();return "{\"ok\":true}";}
  if(cmd.startsWith("cal grams ")) {
    String value=cmd.substring(10);value.trim();
    if(!value.length())return "{\"ok\":false,\"error\":\"invalid_mass\"}";
    for(unsigned i=0;i<value.length();++i) {
      if(!isDigit(value[i]) && value[i]!='.')return "{\"ok\":false,\"error\":\"invalid_mass\"}";
    }
    const float mass=value.toFloat();
    if(!isfinite(mass)||mass<1.0f||mass>100000.0f||!live||strcmp(hxState,"OK")!=0||hxStats.n<3||labs(hxRaw-hxOffset)<100) {
      return "{\"ok\":false,\"error\":\"calibration_precondition\"}";
    }
    hxScale=(hxRaw-hxOffset)/mass;
    return "{\"ok\":true,\"units\":\"g\",\"persistence\":\"ram_only\"}";
  }
  if(cmd=="tare") {
    if(live && (strcmp(hxState,"OK")!=0 || hxStats.n<3)) return "{\"ok\":false,\"error\":\"hx711_not_stable\"}";
    hxOffset=hxRaw;return "{\"ok\":true,\"note\":\"offset_saved_ram_only\"}";
  }
  if(cmd.startsWith("gain ")) {
    String value=cmd.substring(5);value.trim();
    for(unsigned i=0;i<value.length();++i) if(!isDigit(value[i]))return "{\"ok\":false,\"error\":\"bad_gain\"}";
    int gain=value.toInt();if(!value.length()||gain>12)return "{\"ok\":false,\"error\":\"bad_gain\"}";
    spectralGain=gain;
    if(live && spectrumFound && !as7343.setGain(static_cast<as7343_gain_t>(gain))) {specState="FAULT";return "{\"ok\":false,\"error\":\"i2c_write\"}";}
    return "{\"ok\":true}";
  }
  if(cmd.startsWith("interval ")) {
    String value=cmd.substring(9);value.trim();
    for(unsigned i=0;i<value.length();++i) if(!isDigit(value[i]))return "{\"ok\":false,\"error\":\"bad_interval\"}";
    int ms=value.toInt();if(!value.length()||!spirit::validInterval(ms))return "{\"ok\":false,\"error\":\"bad_interval\"}";
    systemIntervalMs=ms;return "{\"ok\":true}";
  }
  return "{\"ok\":false,\"error\":\"unknown_command\"}";
}

void handleButtons(uint32_t now) {
  const bool s=digitalRead(PIN_START)==LOW;
  const bool t=digitalRead(PIN_TARE)==LOW;
  if(s&&!startLast&&now-lastStartEdge>40){acquiring=!acquiring;lastStartEdge=now;}
  if(t&&!tareLast&&now-lastTareEdge>40){if(!live || (strcmp(hxState,"OK")==0 && hxStats.n>=3))hxOffset=hxRaw;lastTareEdge=now;}
  startLast=s;tareLast=t;
}

K_THREAD_STACK_DEFINE(spiritBridgeStack, 8192);
static struct k_thread bridgeThreadData;
void bridgeThreadMain(void*, void*, void*) {
  if (!Bridge.begin()) return;
  bool statusRegistered=Bridge.provide_safe("spirit.status", statusJSON);
  bool commandRegistered=Bridge.provide_safe("spirit.command", command);
  bridgeOk=statusRegistered && commandRegistered;
}

void setup() {
  uptimeStart=millis();
  pinMode(PIN_TRIG,OUTPUT);digitalWrite(PIN_TRIG,LOW);
  pinMode(PIN_ECHO,INPUT);
  pinMode(PIN_HX_SCK,OUTPUT);digitalWrite(PIN_HX_SCK,LOW);
  pinMode(PIN_HX_DOUT,INPUT_PULLUP); // no floating DOUT with disconnected HX711
  pinMode(PIN_START,INPUT_PULLUP);pinMode(PIN_TARE,INPUT_PULLUP);
  pinMode(PIN_BUZZER,OUTPUT);digitalWrite(PIN_BUZZER,LOW);
  Wire.begin();
  setMode(false); // startup safe: no peripheral command is sent until explicitly live
  // Bridge startup runs in a separate Zephyr thread so loss of the
  // Linux router cannot block local sensor acquisition at boot.
  k_thread_create(&bridgeThreadData, spiritBridgeStack,
      K_THREAD_STACK_SIZEOF(spiritBridgeStack), bridgeThreadMain,
      nullptr, nullptr, nullptr, 7, 0, K_NO_WAIT);
  lastClock=k_uptime_get_32();lastTick=lastClock;
}

void loop() {
  uint32_t now=millis();
  const uint32_t clock=k_uptime_get_32();
  if(lastClock!=clock) {jitterStats.add(static_cast<double>(clock-lastClock));lastClock=clock;}
  totalTicks++;
  handleButtons(now);
  if(acquiring) {
    if(!live) {
      if(now-lastHeartbeat>=systemIntervalMs) {lastHeartbeat=now;synthTick(now);}
    } else {
      if(now-lastRetry>=DEVICE_RETRY_MS) {lastRetry=now;if(!dsFound||!spectrumFound)probeDevices();}
      if(!prototypeProfile && now-lastHX>=HX_READY_PERIOD_MS){lastHX=now;updateHX(now);}
      if(!prototypeProfile && now-lastUS>=US_PERIOD_MS){lastUS=now;updateUS();}
      finishTemperature(now);
      if(!temperatureRequested && now-lastTemp>=TEMP_PERIOD_MS){lastTemp=now;beginTemperature(now);}
      if(now-lastSpec>=SPEC_PERIOD_MS){lastSpec=now;updateSpectral();}
    }
  }
  k_msleep(1); // Zephyr cooperative yield; processing rates measured, not guaranteed.
}
