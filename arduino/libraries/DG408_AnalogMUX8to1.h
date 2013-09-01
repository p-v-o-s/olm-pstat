/*
  DG408_AnalogMUX8to1.cpp- Library for interacting with the Vishay
                       DG408 Analog Multiplexer 8 channels to 1 port.
  Created by Craig Wm. Versek, 2013-08-30
  Released into the public domain.
*/

#ifndef _DG408_AnalogMUX8to1_H_INCLUDED
#define _DG408_AnalogMUX8to1_H_INCLUDED

#include <Arduino.h>

#define CHANNEL_MIN 1
#define CHANNEL_MAX 8


class DG408_AnalogMUX8to1Class {
public:
  DG408_AnalogMUX8to1Class(int addr0,
                           int addr1,
                           int addr2,
                           int enablePin = -1 //default - use when enable pin has been hard-wired to HIGH
                         );
  //Configuration methods
  void begin(bool enable_state = HIGH); // default start with enable HIGH
  void setEnable(bool state);
  void end();
  //Functionality methods
  int switchChannel(unsigned int N);
private:
  int _addr0;
  int _addr1;
  int _addr2;
  int _enablePin;
};


#endif //_DG408_AnalogMUX8to1_H_INCLUDED
