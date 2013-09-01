/*
  MCP4xx1_DIGPOT8bit_test.ino - Library for interacting with the Microchip
                       MCP4[12]x1 8-Bit Digital Single (41x1) and Dual (42x1)
                       Potentiometers with SPI Interface.
  Created by Craig Wm. Versek, 2013-07-04
  Released into the public domain.
*/

#include <Arduino.h>
#include <SPI.h>
#include "MCP4xx1_DIGPOT8bit.h"

MCP4xx1_DIGPOT8bitClass::MCP4xx1_DIGPOT8bitClass(int slaveSelectLowPin,
                                                 float maxResistance)
{
  //initialize the pin mapping
  _slaveSelectLowPin = slaveSelectLowPin;
  _wiper0Setting     = -1;
  _wiper1Setting     = -1;
  _maxResistance     = maxResistance;
}

void MCP4xx1_DIGPOT8bitClass::begin()
{
  // Configure the Arduino pins
  pinMode(_slaveSelectLowPin, OUTPUT);
  //comm. off
  digitalWrite(_slaveSelectLowPin, HIGH);
}

void MCP4xx1_DIGPOT8bitClass::end()
{
  //turn all pins off
  digitalWrite(_slaveSelectLowPin, LOW);
}

int MCP4xx1_DIGPOT8bitClass::readWiper0()
{
  return _wiper0Setting;
}

int MCP4xx1_DIGPOT8bitClass::readWiper1()
{
  return _wiper1Setting;
}

int MCP4xx1_DIGPOT8bitClass::writeVolatileWiper0(unsigned int N)
{
  //Volatile Wiper 0 addr = 00h
  //Write command 00h
  word packet = 0x0000;
  
  packet |= 0x01FF & N;  //place wiper setting in lower byte plus 1 bit
  //Serial.println(packet);
  digitalWrite(_slaveSelectLowPin, LOW);   //set chip as listener
  SPI.transfer(highByte(packet));          //send packet
  SPI.transfer(lowByte(packet));
  digitalWrite(_slaveSelectLowPin, HIGH);  //release chip select
  //cache the current setting
  _wiper0Setting = (int) N;
  return 0;
}

int MCP4xx1_DIGPOT8bitClass::writeVolatileWiper1(unsigned int N)
{
  //Volatile Wiper 1 addr = 01h
  //Write command 00h
  word packet = 0x0100;
  
  packet |= 0x01FF & N;  //place wiper setting in lower byte plus 1 bit
  //Serial.println(packet);
  digitalWrite(_slaveSelectLowPin, LOW);   //set chip as listener
  SPI.transfer(highByte(packet));          //send packet
  SPI.transfer(lowByte(packet));
  digitalWrite(_slaveSelectLowPin, HIGH);  //release chip select
  //cache the current setting
  _wiper1Setting = (int) N;
  return 0;
}
