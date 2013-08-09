/*
  MCP320x_ADC12bit_test.ino - Arduino Library Example sketch for the Microchip 
                       MCP3204 & MCP3208 12-Bit Analog to Digital Converter with 
                       SPI 
  Created by Craig Wm. Versek, 2013-08-04
  Released into the public domain.
*/

#include <SPI.h>
#include <MCP320x_ADC12bit.h>

#define DELAY_ms 2000

//configure the DAC chip
MCP320x_ADC12bitClass mADC(5,   //slaveSelectLowPin
                           3.29 //reference voltage
                          );


void setup() {
  Serial.begin(9600);
  //start up the SPI bus
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0);
  //start controlling the voltage supply
  mADC.begin();
}

void loop() {
  float data;
  data = mADC.readSingle(0);
  Serial.print("data0 = ");
  Serial.println(data);
  data = mADC.readSingle(1);
  Serial.print("data1 = ");
  Serial.println(data);
  data = mADC.readSingle(2);
  Serial.print("data2 = ");
  Serial.println(data);
  data = mADC.readSingle(3);
  Serial.print("data3 = ");
  Serial.println(data);
  delay(DELAY_ms);
}
