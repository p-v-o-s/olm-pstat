/*
  MCP4921_DAC12bit.cpp - Library for interacting with the Microchip MCP4921 
                         12-Bit Voltage Output Digital-to-Analog Converter
                         with SPI Interface.
  Created by Craig Wm. Versek, 2013-05-29
  Released into the public domain.
 */

#include <SPI.h>
#include "MCP4921_DAC12bit.h"

MCP4921_DAC12bitClass::MCP4921_DAC12bitClass(int slaveSelectLowPin,
                                             int ldacLowPin,
                                             int shutdownLowPin
                                            ){
  //initialize the pin mapping
  _slaveSelectLowPin = slaveSelectLowPin;
  _ldacLowPin        = ldacLowPin;
  _shutdownLowPin    = shutdownLowPin;
}

void MCP4921_DAC12bitClass::begin() {
  // Configure the Arduino pins
  pinMode(_shutdownLowPin, OUTPUT);
  pinMode(_slaveSelectLowPin, OUTPUT);
  pinMode(_ldacLowPin, OUTPUT);
  
  digitalWrite(_shutdownLowPin, HIGH);     //activate
  digitalWrite(_slaveSelectLowPin, HIGH);  //comm. off
  digitalWrite(_ldacLowPin, HIGH);         //latch off
}

void MCP4921_DAC12bitClass::end() {
  //turn all pins off
  digitalWrite(_shutdownLowPin, LOW);
  digitalWrite(_slaveSelectLowPin, LOW);
  digitalWrite(_ldacLowPin, LOW);
}

int MCP4921_DAC12bitClass::setVoltageOutput(float voltage){
  int              gain_bit = 0;
  unsigned int  volt_digits = 0;
  word packet = 0;
  
  //choose smallest possible range
  if(voltage < VREF){ 
    gain_bit = 1; 
    volt_digits = int( voltage/VREF*RES12BIT );
  }     
  else{ 
    gain_bit = 0; 
    volt_digits = int( 0.5*voltage/VREF*RES12BIT );
  }     
  
  packet = volt_digits << 4;  //shift voltage setting digits
  packet |= 1 << 12;          //add software activate
  packet |= gain_bit << 13;   //add gain setting
  
  digitalWrite(_slaveSelectLowPin, LOW);   //set chip as listener
  SPI.transfer(highByte(packet));          //send packet
  SPI.transfer(lowByte(packet));
  digitalWrite(_slaveSelectLowPin, HIGH);  //release chip select
  digitalWrite(_ldacLowPin, LOW);          //pull latch down
  delayMicroseconds(1);
  digitalWrite(_ldacLowPin, HIGH);         //pull latch up
  
  return 0;
}
