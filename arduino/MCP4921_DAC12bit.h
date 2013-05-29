/*
  MCP4921_DAC12bit.h - Library for interacting with the Microchip MCP4921 
                       12-Bit Voltage Output Digital-to-Analog Converter
                       with SPI Interface.
  Created by Craig Wm. Versek, 2013-05-29
  Released into the public domain.
 */

#ifndef _MCP4921_DAC12bit_H_INCLUDED
#define _MCP4921_DAC12bit_H_INCLUDED

#include <Arduino.h>
//#include <avr/pgmspace.h>

#define VREF 2.048
#define RES12BIT 4096

class MCP4921_DAC12bitClass {
public:
  MCP4921_DAC12bitClass(int slaveSelectLowPin,
                        int ldacLowPin,
                        int shutdownLowPin
                       );
  //Configuration methods
  void begin(); // Default
  void end();
  //Functionality methods
  int setVoltageOutput(float voltage);
private:
  int _shutdownLowPin;
  int _slaveSelectLowPin;
  int _ldacLowPin;
};


#endif //_MCP4921_DAC12bit_H_INCLUDED
