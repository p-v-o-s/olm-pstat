/*
  MCP4xx1_DIGPOT8bit_test.ino - Library for interacting with the Microchip
                       MCP4[12]x1 8-Bit Digital Single (41x1) and Dual (42x1)
                       Potentiometers with SPI Interface.
  Created by Craig Wm. Versek, 2013-07-04
  Released into the public domain.
*/

#include <SPI.h>
#include <MCP4xx1_DIGPOT8bit.h>

#define R_MAX 1e5
#define NUM_STEPS 20
#define DELAY_ms  2000
#define STEP_SIZE RES8BIT/NUM_STEPS

//configure the DAC chip
MCP4xx1_DIGPOT8bitClass digPot(5,    //slaveSelectLowPin
                               R_MAX //maxResistance
                              );


void setup() {
  Serial.begin(9600);
  //start up the SPI bus                   
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0);
  //start controlling the voltage supply
  digPot.begin();
}

void loop() {
  unsigned int N;
  // if there's any serial available, read it:
/*  while (Serial.available() > 0){*/
/*      N = Serial.parseInt();*/
/*      while (Serial.read() != '\n'){};*/
/*      Serial.print("wiper0 = ");*/
/*      Serial.println(N);*/
/*      digPot.writeVolatileWiper0(N);*/
/*  }*/
  for (int i=0; i <= NUM_STEPS; i++){
    N = STEP_SIZE*i;
    digPot.writeVolatileWiper0(N);
    Serial.print("N = ");      
    Serial.println(N);
    while (Serial.read() != '\n'){};
  }  
}
