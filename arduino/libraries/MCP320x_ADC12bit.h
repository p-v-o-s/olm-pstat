/*
  MCP320x_ADC12bit.h - Library for interacting with the Microchip MCP3204 & 
                       MCP3208 12-Bit Analog to Digital Converter with SPI 
                       Interface.
  Created by Craig Wm. Versek, 2013-08-04
  Released into the public domain.
 */

#ifndef _MCP320x_ADC12bit_H_INCLUDED
#define _MCP320x_ADC12bit_H_INCLUDED

#include <Arduino.h>
//#include <avr/pgmspace.h>

#define VREF_MAX 5.46 /*Vdd_MAX - 0.04 V */ 
#define RES12BIT 4096

class MCP320x_ADC12bitClass {
public:
  MCP320x_ADC12bitClass(int slaveSelectLowPin,
                        float refVoltage
                       );
  //Configuration methods
  void begin();
  //Functionality methods
  int setVoltageReference(float voltage);
  float readSingle(int channel);
  int readRawSingle(int channel);
private:
  int   _slaveSelectLowPin;
  float _refVoltage;
};


#endif //_MCP320x_ADC12bit_H_INCLUDED
