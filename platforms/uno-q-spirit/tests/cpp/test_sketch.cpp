#include <cassert>
#include <iostream>
#include "../../UNO_Q_Spirit/UNO_Q_Spirit.ino"
int main(){
  setup();
  assert(!live && bridgeOk);
  assert(statusJSON().str().find("\"mode\":\"synthetic\"")!=std::string::npos);
  for(int i=0;i<2500;i++)loop();
  assert(successTemp>=2);
  assert(hxState==std::string("SYNTH"));
  assert(command("interval 99").str().find("false")!=std::string::npos);
  assert(command("gain 13").str().find("false")!=std::string::npos);
  assert(command("tare").str().find("true")!=std::string::npos);
  assert(command("mode live").str().find("true")!=std::string::npos);
  for(int i=0;i<8000;i++)loop();
  assert(!dsFound && !spectrumFound);
  assert(std::string(tempState)=="MISSING");
  assert(std::string(specState)=="MISSING");
  assert(std::string(hxState)=="TIMEOUT");
  assert(std::string(usState)=="TIMEOUT");
  assert(command("tare").str().find("false")!=std::string::npos);
  assert(command("profile prototype").str().find("true")!=std::string::npos);
  assert(statusJSON().str().find("\"profile\":\"prototype\"")!=std::string::npos);
  for(int i=0;i<500;i++)loop();
  assert(std::string(hxState)=="DISABLED");
  assert(std::string(usState)=="DISABLED");
  assert(command("profile all").str().find("true")!=std::string::npos);
  assert(std::string(hxState)=="WARMUP");
  assert(command("mode synthetic").str().find("true")!=std::string::npos);
  assert(std::string(tempState)=="SYNTH");
  assert(command("no such command").str().find("false")!=std::string::npos);
  std::cout<<"PASS: sketch simulation (absent sensor, mock bridge, commands)\n";
}
