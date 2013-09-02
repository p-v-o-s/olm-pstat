/*
  DG408_AnalogMUX8to1.ino. - Library for interacting with the Vishay
                       DG408 Analog Multiplexer 8 channels to 1 port.
  Created by Craig Wm. Versek, 2013-08-30
  Released into the public domain.
*/


#include <SPI.h>
#include <DG408_AnalogMUX8to1.h>

//configure the MUX chip - on OLM port 4
DG408_AnalogMUX8to1Class MUX(10,  //addr0
                             A3, //addr1
                             7   //addr2
                            );


void setup() {
  Serial.begin(9600);
  //start up the SPI bus
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0);
  //start controlling the voltage supply
  MUX.begin();
}

void loop() {
  for (int i = CHANNEL_MIN; i <= CHANNEL_MAX; i++){
    Serial.print("Switching to channel ");
    Serial.println(i);
    MUX.switchChannel(i);
    while (Serial.read() != '\n'){};
  }  
}
