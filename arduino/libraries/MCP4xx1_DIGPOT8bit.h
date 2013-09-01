/*
  MCP4xx1_DIGPOT8bit_test.ino - Library for interacting with the Microchip
                       MCP4[12]x1 8-Bit Digital Single (41x1) and Dual (42x1)
                       Potentiometers with SPI Interface.
  Created by Craig Wm. Versek, 2013-07-04
  Released into the public domain.
*/

#ifndef _MCP4xx1_DIGPOT8bit_H_INCLUDED
#define _MCP4xx1_DIGPOT8bit_H_INCLUDED

#include <Arduino.h>

#define RES8BIT 256

class MCP4xx1_DIGPOT8bitClass {
public:
  MCP4xx1_DIGPOT8bitClass(int   slaveSelectLowPin,
                          float maxResistance
                         );
  //Configuration methods
  void begin(); // Default
  void end();
  //Functionality methods
  int writeVolatileWiper0(unsigned int N);
  int writeVolatileWiper1(unsigned int N);
private:
  int   _slaveSelectLowPin;
  int   _wiperSetting;
  float _maxResistance;
};


#endif //_MCP4xx1_DIGPOT8bit_H_INCLUDED
