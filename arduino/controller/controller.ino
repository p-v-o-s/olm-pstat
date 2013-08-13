/*
  Created by Craig Wm. Versek, 2013-08-09
  Released into the public domain.
*/

#include <SPI.h>
#include <MCP4921_DAC12bit.h>
#include <MCP320x_ADC12bit.h>
//3rd Party Libraries
#include <SerialCommand.h>

#define V_REF  3.29
#define V_VGND V_REF/2.0
#define R_CURRSENSE 1000.0

#define DELTA_V 0.05
#define V_MIN (-V_REF/2.0 + DELTA_V)
#define V_MAX ( V_REF/2.0 - DELTA_V)
#define NUM_STEPS 100
#define DELAY_ms 100

//SerialCommand parser
SerialCommand SCmd;

//configure the DAC chip
MCP4921_DAC12bitClass control_DAC(3,     //slaveSelectLowPin
                                  3,     //ldacLowPin
                                  V_VGND //reference voltage at mid-scale
                                 );
//configure the ADC chip
MCP320x_ADC12bitClass sense_ADC(5,   //slaveSelectLowPin
                                V_REF //reference voltage at full-scale
                              );


void setup() {
  Serial.begin(9600);
  //configure the serial commands
  SCmd.addCommand("VCTRL", setControlVoltageCommand);
  SCmd.addCommand("VSWEEP", doSweepCommand);
  SCmd.setDefaultHandler(unrecognizedCommand);
  //start up the SPI bus
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0);
  //start controlling the voltage supply
  control_DAC.begin();
  //start controlling the sampling
  sense_ADC.begin();
}

void loop() {
  //process serial commands
  SCmd.readSerial();
}

void doSweep() {
  float voltage_step = (V_MAX - V_MIN)/NUM_STEPS;
  float control_voltage;          //referenced to V_VGND
  float RE_voltage;               //referenced to power rails
  float WEtoRE_voltage;           //WE voltage referenced to RE
  float WE_current_sense_voltage; //voltage across current follower sense resistor, ref. to power rails
  float WE_current;               //compute current into WE
  Serial.println("#BEGIN VSWEEP");
  Serial.println("#COLUMNS control_voltage,WEtoRE_voltage,currentWE_in");
  for (int i=0; i <= NUM_STEPS; i++){
    control_voltage = V_MIN + voltage_step*i;
    //change output voltage
    control_DAC.setVoltageOutput(V_REF - (control_voltage + V_VGND)); //shift to center-rail and invert
    //wait for settling
    delay(DELAY_ms);
    //read signals
    RE_voltage               = sense_ADC.readSingle(0);
    WE_current_sense_voltage = sense_ADC.readSingle(1);
    //convert to centerline voltage and correct for inversion
    WEtoRE_voltage =  (RE_voltage - V_VGND);
    WE_current     = -(WE_current_sense_voltage - V_VGND)/R_CURRSENSE;
    //format as YAML
    Serial.print(control_voltage, 6);
    Serial.print(',');
    Serial.print(WEtoRE_voltage, 6);
    Serial.print(',');
    Serial.print(WE_current, 6);
    Serial.print('\n');
    //while (Serial.read() != '\n'){};
  }
  Serial.println("#END VSWEEP");
}

//------------------------------------------------------------------------------
//COMMAND HANDLER FUNCTIONS - called by the SCmd dispatcher

void setControlVoltageCommand(){
  float control_voltage;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    control_voltage = atof(arg);
    if (control_voltage < V_MIN || control_voltage > V_MAX)
    {
      Serial.print("### Error: VCTRL must have (");
      Serial.print(V_MIN,3);
      Serial.print(" <= control_voltage <= ");
      Serial.print(V_MAX,3);
      Serial.print(") ###\n");
    }
    control_DAC.setVoltageOutput(V_REF - (control_voltage + V_VGND)); //shift to center-rail and invert
  }
  else
  {
    Serial.println("### Error: VCTRL - requires 1 argument (float control_voltage) ###");
  }
}

void doSweepCommand(){
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    Serial.println("### Error: VSWEEP requires 0 arguments ###");
  }
  else
  {
    doSweep();
  }
}

void unrecognizedCommand(const char *command)
{
  Serial.println("### Error: command not recognized ###");
}
