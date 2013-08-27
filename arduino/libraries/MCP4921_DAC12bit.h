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

#define VREF_MAX 5.46 /*Vdd_MAX - 0.04 V */ 
#define RES12BIT 4096

class MCP4921_DAC12bitClass {
public:
  MCP4921_DAC12bitClass(int slaveSelectLowPin,
                        int ldacLowPin,
                        float refVoltage
                       );
  //Configuration methods
  void begin(float initVoltage = 0.0); // Default
  void end();
  //Functionality methods
  int   setVoltageReference(float voltage);
  int   setVoltageOutput(float voltage);
  float getVoltageOutput();
private:
  int _slaveSelectLowPin;
  int _ldacLowPin;
  float _refVoltage;
  float _outputVoltage;
};


#endif //_MCP4921_DAC12bit_H_INCLUDED
