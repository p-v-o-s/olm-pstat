/*
  MCP320x_ADC12bit.cpp - Library for interacting with the Microchip MCP4921 
                         12-Bit Voltage Output Digital-to-Analog Converter
                         with SPI Interface.
  Created by Craig Wm. Versek, 2013-05-29
  Released into the public domain.
 */
#include <Arduino.h>
#include <SPI.h>
#include "MCP320x_ADC12bit.h"

MCP320x_ADC12bitClass::MCP320x_ADC12bitClass(int slaveSelectLowPin,
                                             float refVoltage
                                            ){
  _slaveSelectLowPin = slaveSelectLowPin;
  _refVoltage        = 0.0;
  setVoltageReference(refVoltage);
}

void MCP320x_ADC12bitClass::begin() {
  // Configure the Arduino pins
  pinMode(_slaveSelectLowPin, OUTPUT);
  digitalWrite(_slaveSelectLowPin, HIGH);  //comm. off
}

int MCP320x_ADC12bitClass::setVoltageReference(float voltage) {
  if(voltage > 0 && voltage <= VREF_MAX){
    _refVoltage = voltage;
    return 0;
  }
  else{ return -1; }          //error, out of range
}

float MCP320x_ADC12bitClass::readSingle(int channel){
  int data;
  float voltage;
  data = readRawSingle(channel);
  voltage = (data*_refVoltage)/(RES12BIT - 1.0);
  return voltage;
}

int MCP320x_ADC12bitClass::readRawSingle(int channel){
  word cmd;                       //0,0,0,0,0,1,sgl=0,d2    d1,d0,x,x,x,x,x,x
  int data;                       //?,?,?,0,b11,b10,b9,b8   b7,b6,b5,b4,b3,b2,b1,b0
  //configure command
  cmd  =  0b110 << 8;             //start bit, single ended
  cmd |= (channel & 0b111) << 6;  //d2,d1,d0 -- sampling channel
 // Serial.println(cmd);
  digitalWrite(_slaveSelectLowPin, LOW);  //set chip as listener
  SPI.transfer(highByte(cmd));            //send first command byte, ignore first returned byte
  data  = SPI.transfer(lowByte(cmd));     //send second command byte, get data high byte
  data  = (data & 0b1111) << 8;           //b11,b10,b9,b8
  data |= SPI.transfer(0);                //send null byte, get data low byte b7-b0
  digitalWrite(_slaveSelectLowPin, HIGH); //release chip select
  return data;
}
