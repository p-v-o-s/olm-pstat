/*
  DG408_AnalogMUX8to1.cpp. - Library for interacting with the Vishay
                       DG408 Analog Multiplexer 8 channels to 1 port.
  Created by Craig Wm. Versek, 2013-08-30
  Released into the public domain.
*/

#include <Arduino.h>
#include <SPI.h>
#include "DG408_AnalogMUX8to1.h"

DG408_AnalogMUX8to1Class::DG408_AnalogMUX8to1Class(
                                                   int addr0,
                                                   int addr1,
                                                   int addr2,
                                                   int enablePin
                                                  ){
  //initialize the pin mapping
  _addr0 = addr0;
  _addr1 = addr1;
  _addr2 = addr2;
  _enablePin = enablePin;
}

void DG408_AnalogMUX8to1Class::begin(bool enable_state) {
  // Configure the Arduino pins
  pinMode(_addr0, OUTPUT);
  pinMode(_addr1, OUTPUT);
  pinMode(_addr2, OUTPUT);
  if (_enablePin >= 0){
    pinMode(_enablePin, OUTPUT);
    setEnable(enable_state);
  }
}

void DG408_AnalogMUX8to1Class::end() {
  //turn all pins off
  setEnable(false);
  switchChannel(1);
}

void DG408_AnalogMUX8to1Class::setEnable(bool state) {
  if (_enablePin >= 0){
    digitalWrite(_enablePin, state);
  }
}

int DG408_AnalogMUX8to1Class::switchChannel(unsigned int N){
  if (N < CHANNEL_MIN || N > CHANNEL_MAX){
    return -1;
  }
  digitalWrite(_addr0, (N - 1) & 0b001);
  digitalWrite(_addr1, (N - 1) & 0b010);
  digitalWrite(_addr2, (N - 1) & 0b100);
  return 0;
}
