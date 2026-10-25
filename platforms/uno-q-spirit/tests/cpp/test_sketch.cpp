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
  assert(command("mode synthetic").str().find("true")!=std::string::npos);
  assert(std::string(tempState)=="SYNTH");
  assert(command("no such command").str().find("false")!=std::string::npos);
  std::cout<<"PASS: sketch simulation (absent sensor, mock bridge, commands)\n";
}
