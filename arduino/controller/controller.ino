/*
  Created by Craig Wm. Versek, 2013-08-09
  Released into the public domain.
*/

#include <SPI.h>
#include <MCP4921_DAC12bit.h>
#include <MCP320x_ADC12bit.h>
//3rd Party Libraries
#include <SerialCommand.h>
#include <TimerOne.h>      /*fast microsecond timer with interrupts*/
#include <Timer.h>         /*multipurpose timer-multiplexing */

#define BAUDRATE 9600

#define FLOAT_PRECISION_DIGITS 9
#define V_REF  3.29
#define V_VGND V_REF/2.0
#define V_INIT V_VGND
#define R_CURRSENSE 1e4

#define DELTA_V 0.05
#define V_MIN (-V_REF/2.0 + DELTA_V)
#define V_MAX ( V_REF/2.0 - DELTA_V)

//SerialCommand parser
SerialCommand SCmd;

//Sample Timer
Timer SampleTimer;

//configure the DAC chip
MCP4921_DAC12bitClass control_DAC(3,      //slaveSelectLowPin
                                  3,      //ldacLowPin
                                  V_VGND  //reference voltage at mid-scale
                                 );
//configure the ADC chip
MCP320x_ADC12bitClass sense_ADC(5,   //slaveSelectLowPin
                                V_REF //reference voltage at full-scale
                              );


void setup(){
  Serial.begin(BAUDRATE);
  
  //configure the serial commands
  //SCmd.addCommand("*RST",    softwareReset);
  //SCmd.addCommand("STATUS?", getStatusCommand);
  //SCmd.addCommand("VCELL?",  getCellVoltageCommand);
  //SCmd.addCommand("ICELL?",  getCellCurrentCommand);
 // SCmd.addCommand("VCTRL",   setControlVoltageCommand);
  SCmd.addCommand("VSWEEP",  doSweepCommand);
  SCmd.addCommand("VSWEEP_START",  setSweepStartCommand);
  SCmd.addCommand("VSWEEP_END",    setSweepEndCommand);
  SCmd.addCommand("VSWEEP_RAMP",   setSweepRampCommand);
  SCmd.addCommand("VSWEEP_SAMPLE", setSweepSampleRateCommand);
  //SCmd.addCommand("VSWEEP_CYCLES", setSweepCyclesCommand);
  
  SCmd.setDefaultHandler(unrecognizedCommand);
  Serial.print("#<INIT>\n");
  //start up the SPI bus
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0);
  //start controlling the voltage supply
  control_DAC.begin(V_INIT);
  //start controlling the sampling
  sense_ADC.begin();
  Serial.print("#OLM Potentiostat v0.1\n");
  Serial.print("#</INIT>\n");
}

void loop(){
  //process serial commands
  SCmd.readSerial();
}

void softwareReset() // Restarts program from beginning but does not reset the peripherals and registers
{
  asm volatile ("  jmp 0");
}

//------------------------------------------------------------------------------
// VOLTAGE SWEEP
#define SWEEP_UPDATE_PERIOD 300 /* microseconds */

#define SAMPRATE_MIN 1.0
#define SAMPRATE_MAX 100.0
#define SAMPRATE_DEFAULT 10.0

float _sweep_voltage_step;
volatile float _sweep_control_voltage;

//default parameters for the sweep
float _sweep_v_start =  0;
float _sweep_v_end   =  1.5;
float _sweep_v_rate  =  0.25;              //volts per sec
float _sweep_samp_rate = SAMPRATE_DEFAULT; //samples per second
float _sweep_cycles  =  1;

void sweepTickISR(){
    //Serial.print("Tick!\n");
    _sweep_control_voltage += _sweep_voltage_step;
    noInterrupts();           // disable all interrupts
    //change output voltage
    control_DAC.setVoltageOutput(_sweep_control_voltage + V_VGND); //shift to center-rail
    interrupts();           // enable interrupts
}

void sweepSampleCallback(){
    float RE_voltage;               //referenced to power rails
    float WEtoRE_voltage;           //WE voltage referenced to RE
    float WE_current_sense_voltage; //voltage across current follower sense resistor, ref. to power rails
    float WE_current;               //compute current into WE

    noInterrupts();           // disable all interrupts
    //read signals
    RE_voltage               = sense_ADC.readSingle(0);
    WE_current_sense_voltage = sense_ADC.readSingle(1);
    interrupts();           // enable interrupts
    //convert to centerline voltage and correct for inversion
    WEtoRE_voltage = -(RE_voltage - V_VGND);
    WE_current     = -(WE_current_sense_voltage - V_VGND)/R_CURRSENSE;
    //format as CSV
    Serial.print(_sweep_control_voltage, FLOAT_PRECISION_DIGITS);
    Serial.print(',');
    Serial.print(WEtoRE_voltage, FLOAT_PRECISION_DIGITS);
    Serial.print(',');
    Serial.print(WE_current, FLOAT_PRECISION_DIGITS);
    Serial.print('\n');
}


  
void doSweep(){
  _sweep_control_voltage = _sweep_v_start; //referenced to V_VGND
  _sweep_voltage_step    = _sweep_v_rate*1e-6*SWEEP_UPDATE_PERIOD;
 
  Serial.print("#<VSWEEP>\n");
  Serial.print("#<METADATA>\n");
  Serial.print("#start_voltage: ");
  Serial.print(_sweep_v_start, FLOAT_PRECISION_DIGITS);
  Serial.print("\n");
  Serial.print("#end_voltage: ");
  Serial.print(_sweep_v_end, FLOAT_PRECISION_DIGITS);
  Serial.print("\n");
  Serial.print("#voltage_ramp_rate: ");
  Serial.print(_sweep_v_rate, FLOAT_PRECISION_DIGITS);
  Serial.print("\n");
  Serial.print("#sample_rate: ");
  Serial.print(_sweep_samp_rate, FLOAT_PRECISION_DIGITS);
  Serial.print("\n");
  Serial.print("#update_period: ");
  Serial.print(1e-6*SWEEP_UPDATE_PERIOD, FLOAT_PRECISION_DIGITS);
  Serial.print("\n");
  Serial.print("#voltage_step: ");
  Serial.print(_sweep_voltage_step, FLOAT_PRECISION_DIGITS);
  Serial.print("\n");
  Serial.print("#</METADATA>\n");
  Serial.print("#<COLUMNS>control_voltage,WEtoRE_voltage,currentWE_in</COLUMNS>\n");
  Serial.print("#<CSV_DATA>\n");
  //begin the timer loop
  Timer1.initialize(SWEEP_UPDATE_PERIOD); // initialize timer1 to period [us]
  Timer1.attachInterrupt(sweepTickISR);  // call this function on every tick of Timer1
  //start up the sampling clock
  int sample_period = (int) (1000.0/_sweep_samp_rate);
  int sampleEvent = SampleTimer.every(sample_period, sweepSampleCallback); //milliseconds
  int i;
  for(i=0; i < _sweep_cycles; i++){
      while (_sweep_control_voltage <= _sweep_v_end){
        SampleTimer.update();
      }
      _sweep_voltage_step = -1.0*_sweep_voltage_step;
      while (_sweep_control_voltage >= _sweep_v_start){
        SampleTimer.update();
      }
      _sweep_voltage_step = -1.0*_sweep_voltage_step;
  }
  SampleTimer.stop(sampleEvent);
  Serial.print("#</CSV_DATA>\n");
  Serial.print("#</VSWEEP>\n");
  Timer1.detachInterrupt();
}

//------------------------------------------------------------------------------
//COMMAND HANDLER FUNCTIONS - called by the SCmd dispatcher

void getStatusCommand(){
  float control_voltage;          //referenced to V_VGND
  float RE_voltage;               //referenced to power rails
  float WEtoRE_voltage;           //WE voltage referenced to RE
  float WE_current_sense_voltage; //voltage across current follower sense resistor, ref. to power rails
  float WE_current;               //compute current into WE
  float offset_voltage;           //referenced to power rails
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    Serial.println("### Error: STATUS? - requires 0 arguments ###");
  }
  else
  {
    control_voltage = control_DAC.getVoltageOutput() - V_VGND; //shift back from center-rail
    //read signals
    RE_voltage               = sense_ADC.readSingle(0);
    WE_current_sense_voltage = sense_ADC.readSingle(1);
    offset_voltage           = sense_ADC.readSingle(2);
    //convert to centerline voltage
    WEtoRE_voltage = -(RE_voltage - V_VGND);
    //sesning current flows in opposite direction to current flowing into WE
    WE_current     = -(WE_current_sense_voltage - V_VGND)/R_CURRSENSE;
    //format as YAML
    Serial.print("#<STATUS>\n");
    Serial.print("---\n");
    Serial.print("control_voltage: ");
    Serial.print(control_voltage, FLOAT_PRECISION_DIGITS);
    Serial.print('\n');
    Serial.print("WEtoRE_voltage: ");
    Serial.print(WEtoRE_voltage, FLOAT_PRECISION_DIGITS);
    Serial.print('\n');
    Serial.print("WE_current: ");
    Serial.print(WE_current, FLOAT_PRECISION_DIGITS);
    Serial.print('\n');
    Serial.print("offset_voltage: ");
    Serial.print(offset_voltage, FLOAT_PRECISION_DIGITS);
    Serial.print('\n');
    Serial.print("#</STATUS>\n");
  }
}

void getCellVoltageCommand(){
  float RE_voltage;               //referenced to power rails
  float WEtoRE_voltage;           //WE voltage referenced to RE
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    Serial.println("### Error: VCELL? - requires 0 arguments ###");
  }
  else
  {
    //read signal
    RE_voltage     = sense_ADC.readSingle(0);
    //convert to centerline voltage
    WEtoRE_voltage = -(RE_voltage - V_VGND);
    //print out value
    Serial.print(WEtoRE_voltage, FLOAT_PRECISION_DIGITS);
    Serial.print('\n');
  }
}

void getCellCurrentCommand(){
  float WE_current_sense_voltage; //voltage across current follower sense resistor, ref. to power rails
  float WE_current;               //compute current into WE
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    Serial.println("### Error: ICELL? - requires 0 arguments ###");
  }
  else
  {
    //read signal
    WE_current_sense_voltage = sense_ADC.readSingle(1);
    //convert to centerline voltage and correct for inversion
    WE_current     = -(WE_current_sense_voltage - V_VGND)/R_CURRSENSE;
    //print out value
    Serial.print(WE_current, FLOAT_PRECISION_DIGITS);
    Serial.print('\n');
  }
}

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
      return;
    }
    control_DAC.setVoltageOutput(control_voltage + V_VGND); //shift to center-rail
  }
  else
  {
    Serial.println("### Error: VCTRL - requires 1 argument (float control_voltage) ###");
  }
}

//------------------------------------------------------------------------------
//VSWEEP commands

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

void setSweepStartCommand(){
  float v_start;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    v_start = atof(arg);
    if (v_start < V_MIN || v_start > V_MAX)
    {
      Serial.print("### Error: VSWEEP_START must have (");
      Serial.print(V_MIN,3);
      Serial.print(" <= v_start <= ");
      Serial.print(V_MAX,3);
      Serial.print("), got:");
      Serial.print(v_start,3);
      Serial.print(" ###\n");
      return;
    }
    _sweep_v_start = v_start;
  }
  else
  {
    Serial.println("### Error: VSWEEP_START - requires 1 argument (float v_start) ###");
  }
}

void setSweepEndCommand(){
  float v_end;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    v_end = atof(arg);
    if (v_end < V_MIN || v_end > V_MAX)
    {
      Serial.print("### Error: VSWEEP_END must have (");
      Serial.print(V_MIN,3);
      Serial.print(" <= v_end <= ");
      Serial.print(V_MAX,3);
      Serial.print(") ###\n");
      return;
    }
    _sweep_v_end = v_end;
  }
  else
  {
    Serial.println("### Error: VSWEEP_END - requires 1 argument (float v_end) ###");
  }
}

void setSweepRampCommand(){
  float v_rate;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    v_rate = atof(arg);
    if (v_rate < V_MIN || v_rate > V_MAX)
    {
      Serial.print("### Error: VSWEEP_RAMP must have (");
      Serial.print(V_MIN,3);
      Serial.print(" <= v_rate <= ");
      Serial.print(V_MAX,3);
      Serial.print(") ###\n");
      return;
    }
    _sweep_v_rate = v_rate;
  }
  else
  {
    Serial.println("### Error: VSWEEP_RAMP - requires 1 argument (float v_rate) ###");
  }
}

void setSweepSampleRateCommand(){
  float samp_rate;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    samp_rate = atof(arg);
    if (samp_rate < V_MIN || samp_rate > V_MAX)
    {
      Serial.print("### Error: VSWEEP_SAMPLE must have (");
      Serial.print(SAMPRATE_MIN,3);
      Serial.print(" <= samp_rate <= ");
      Serial.print(SAMPRATE_MAX,3);
      Serial.print(") ###\n");
      return;
    }
    _sweep_samp_rate = samp_rate;
  }
  else
  {
    Serial.println("### Error: VSWEEP_SAMPLE - requires 1 argument (float samp_rate) ###");
  }
}

void setSweepCyclesCommand(){
  int cycles;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    cycles = atoi(arg);
    _sweep_cycles = cycles;
  }
  else
  {
    Serial.println("### Error: VSWEEP_CYCLES- requires 1 argument (int cycles) ###");
  }
}

//------------------------------------------------------------------------------

// Unrecognized command
void unrecognizedCommand(const char *command)
{
  Serial.println("### Error: command not recognized ###");
}
