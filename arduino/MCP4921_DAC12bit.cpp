/*
  MCP4921_DAC12bit.cpp - Library for interacting with the Microchip MCP4921 
                         12-Bit Voltage Output Digital-to-Analog Converter
                         with SPI Interface.
  Created by Craig Wm. Versek, 2013-05-29
  Released into the public domain.
 */
#include <Arduino.h>
#include <SPI.h>
#include "MCP4921_DAC12bit.h"

MCP4921_DAC12bitClass::MCP4921_DAC12bitClass(int slaveSelectLowPin,
                                             int ldacLowPin,
                                             float refVoltage
                                            ){
  //initialize the pin mapping
  _slaveSelectLowPin = slaveSelectLowPin;
  _ldacLowPin        = ldacLowPin;
  _refVoltage        = 0.0;
  setVoltageReference(refVoltage);
}

void MCP4921_DAC12bitClass::begin() {
  // Configure the Arduino pins
  pinMode(_slaveSelectLowPin, OUTPUT);
  pinMode(_ldacLowPin, OUTPUT);
  
  digitalWrite(_slaveSelectLowPin, HIGH);  //comm. off
  digitalWrite(_ldacLowPin, HIGH);         //latch off
}

void MCP4921_DAC12bitClass::end() {
  //turn all pins off
  digitalWrite(_slaveSelectLowPin, LOW);
  digitalWrite(_ldacLowPin, LOW);
}

int MCP4921_DAC12bitClass::setVoltageReference(float voltage) {
  if(voltage > 0 && voltage <= VREF_MAX){
    _refVoltage = voltage;
    return 0;
  }
  else{ return -1; }
}

int MCP4921_DAC12bitClass::setVoltageOutput(float voltage){
  int              gain_bit = 0;
  unsigned int  volt_digits = 0;
  word packet = 0;
  
  //choose smallest possible range
  if(voltage < _refVoltage){ 
    gain_bit = 1; 
    volt_digits = int( voltage/_refVoltage*RES12BIT );
  }     
  else{ 
    gain_bit = 0; 
    volt_digits = int( 0.5*voltage/_refVoltage*RES12BIT );
  }     
  
  packet = volt_digits << 0;  //shift voltage setting digits
  packet |= 1 << 12;          //add software activate
  packet |= gain_bit << 13;   //add gain setting
  packet |= 1 << 14;          //set buffered mode
  Serial.println(packet);
  digitalWrite(_slaveSelectLowPin, LOW);   //set chip as listener
  SPI.transfer(highByte(packet));          //send packet
  SPI.transfer(lowByte(packet));
  digitalWrite(_slaveSelectLowPin, HIGH);  //release chip select
  digitalWrite(_ldacLowPin, LOW);          //pull latch down
  delayMicroseconds(1);
  digitalWrite(_ldacLowPin, HIGH);         //pull latch up
  
  return 0;
}
