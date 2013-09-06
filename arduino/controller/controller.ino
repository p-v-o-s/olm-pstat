/*
  Created by Craig Wm. Versek, 2013-08-09
  Released into the public domain.
*/

#include <SPI.h>
#include <MCP4921_DAC12bit.h>
#include <MCP320x_ADC12bit.h>
#include <MCP4xx1_DIGPOT8bit.h>
#include <DG408_AnalogMUX8to1.h>
//3rd Party Libraries
#include <SerialCommand.h>
#include <TimerOne.h>      /*fast microsecond timer with interrupts*/
#include <Timer.h>         /*multipurpose timer-multiplexing */

//Communication
#define BAUDRATE 115200
#define FLOAT_PRECISION_DIGITS 9
#define FLOAT_DELTA 1e-20
#define MAXCOMMANDS 12

//Voltage sensing
#define ADC_CHANNEL_VOLTAGE 0
#define V_REF  3.297
#define V_VGND V_REF/2.0
#define V_INIT V_VGND

//Current sensing
#define ADC_CHANNEL_CURRENT 1
#define ADC_CHANNEL_CURRENT_OFFSET 2
#define DIGPOT_N_INIT 128
#define CURRSENSE_RANGE_MIN 0
#define CURRSENSE_RANGE_MAX 4

const float _currsense_resistors[]       = {250.0 ,2.50e3,25.0e3 ,250e3  ,2.50e6};      //Ohms
const float _currsense_autotransitions[] = {4.0e-3,400e-6,40.0e-6,4.00e-6,400e-9, 0.0}; //Amps; last value prevents out of array bounds indexing for autoranging procedure
volatile int _currsense_range = 0;
bool         _currsense_auto  = false;

//VSWEEP control
#define DELTA_V 0.05
#define V_MIN (-V_REF/2.0 + DELTA_V)
#define V_MAX ( V_REF/2.0 - DELTA_V)

//SerialCommand parser
SerialCommand SCmd(MAXCOMMANDS);

//Sample Timer
Timer SampleTimer;

//configure the DAC chip - on OLM port 2
MCP4921_DAC12bitClass control_DAC(3,      //slaveSelectLowPin
                                  3,      //ldacLowPin
                                  V_VGND  //reference voltage at mid-scale
                                 );
//configure the ADC chip - on OLM port 2
MCP320x_ADC12bitClass sense_ADC(5,   //slaveSelectLowPin
                                V_REF //reference voltage at full-scale
                              );

//configure the DIGPOT chip - on OLM port 2
MCP4xx1_DIGPOT8bitClass  offset_DIGPOT(A1,    //slaveSelectLowPin
                                       100e3  //maxResistance
                                      );

//configure the MUX chip - on OLM port 4
DG408_AnalogMUX8to1Class currsense_MUX(10, //addr0
                                       A3, //addr1
                                       7   //addr2
                                      );


void setup(){
  Serial.begin(BAUDRATE);
  
  //configure the serial commands
  //SCmd.addCommand("*IDN?",   identify);
  SCmd.addCommand("*RST",    softwareReset);
  
  
  SCmd.addCommand("STATUS?", getStatusCommand);
  SCmd.addCommand("VCELL?",  getCellVoltageCommand);
  SCmd.addCommand("ICELL?",  getCellCurrentCommand);
  
  SCmd.addCommand("IRANGE.LEVEL",  setCurrentRangeLevelCommand);
  SCmd.addCommand("IRANGE.AUTO",   setCurrentRangeAutoCommand);
  
  SCmd.addCommand("VCTRL",   setControlVoltageCommand);
  
  SCmd.addCommand("VSWEEP!",       doSweepCommand); 
  SCmd.addCommand("VSWEEP.START",  setSweepStartCommand);
  SCmd.addCommand("VSWEEP.END",    setSweepEndCommand);
  SCmd.addCommand("VSWEEP.RAMP",   setSweepRampCommand);
  SCmd.addCommand("VSWEEP.SAMPLE", setSweepSampleRateCommand);
  SCmd.addCommand("VSWEEP.CYCLES", setSweepCyclesCommand);

  SCmd.setDefaultHandler(unrecognizedCommand);
  Serial.print(F("#<INIT>\n"));
  //start up the SPI bus
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0);
  //configure the offset to the centerline
  offset_DIGPOT.begin();
  offset_DIGPOT.writeVolatileWiper0(DIGPOT_N_INIT);
  //start the current range MUX switching to highest range
  currsense_MUX.begin();
  switchCurrentSenseRange(0);
  //start controlling the voltage supply
  control_DAC.begin(V_INIT);
  //start controlling the sampling
  sense_ADC.begin();
  Serial.print(F("# OLM Potentiostat v0.1\n"));
  Serial.print(F("# memory_free = "));
  Serial.print(memoryFree());
  Serial.print(F("\n"));
  Serial.print(F("#</INIT>\n"));
}

void loop(){
  //process serial commands
  SCmd.readSerial();
}

//------------------------------------------------------------------------------
// FUNCTIONS

// variables created by the build process when compiling the sketch
extern int __bss_end;
extern void *__brkval;

// function to return the amount of free RAM
int memoryFree()
{
  int freeValue;

  if ((int)__brkval == 0)
     freeValue = ((int)&freeValue) - ((int)&__bss_end);
  else
    freeValue = ((int)&freeValue) - ((int)__brkval);

  return freeValue;
}

void softwareReset() // Restarts program from beginning but does not reset the peripherals and registers
{
  asm volatile ("  jmp 0");
} 

void switchCurrentSenseRange(int range_index)
{
  currsense_MUX.switchChannel(range_index + 1);
  _currsense_range = range_index;
}

float measureCellVoltage()
{
  float RE_voltage;               //referenced to power rails
  float WEtoRE_voltage;           //WE voltage referenced to RE
  //read signal
  RE_voltage = sense_ADC.readSingle(ADC_CHANNEL_VOLTAGE);
  //convert to centerline voltage
  WEtoRE_voltage = -(RE_voltage - V_VGND);
  return WEtoRE_voltage;
}

float measureCellCurrent()
{
  float WE_current_sense_voltage; //voltage across current follower sense resistor, ref. to power rails
  float WE_current;               //compute current into WE
  float current_sense_resistance = _currsense_resistors[_currsense_range];
  //read signal
  WE_current_sense_voltage = sense_ADC.readSingle(ADC_CHANNEL_CURRENT) - V_VGND;
  //convert to centerline voltage and correct for inversion
  WE_current = -WE_current_sense_voltage/current_sense_resistance;
  //now take care of autoranging
  if (_currsense_auto == true)
  {
    //--------------------------------------------------------------------------
    while (true)
    {
      //out of range upper range
      if (abs(WE_current) > _currsense_autotransitions[_currsense_range])
      {
        //if we are not at the lowest range
        if (_currsense_range > CURRSENSE_RANGE_MIN)
        {
          switchCurrentSenseRange(_currsense_range - 1);
          Serial.print(F("#<AUTORANGE value = "));
          Serial.print(_currsense_range);
          Serial.print(F("/>\n"));
          delay(100);
        }
        else{ Serial.print(F("#IN ELSE1\n"));break; }
      }
      //out of lower range
      else if (abs(WE_current) < _currsense_autotransitions[_currsense_range + 1])
      {
        if (_currsense_range < CURRSENSE_RANGE_MAX)
        {
          switchCurrentSenseRange(_currsense_range + 1);
          Serial.print(F("#<AUTORANGE value = "));
          Serial.print(_currsense_range);
          Serial.print(F("/>\n"));
        }
        else{ Serial.print(F("#IN ELSE2\n"));break; }
      }
      //we are in range
      else
      { 
        Serial.print(F("#IN ELSE3\n"));
        break;
      }
      //resample
      current_sense_resistance = _currsense_resistors[_currsense_range];
      WE_current_sense_voltage = sense_ADC.readSingle(ADC_CHANNEL_CURRENT) - V_VGND;
      WE_current = -WE_current_sense_voltage/current_sense_resistance;
      Serial.print(F("#<RESAMPLE WE_current = "));
      Serial.print(WE_current, FLOAT_PRECISION_DIGITS);
      Serial.print(F("/>\n"));
    }
  }
  return WE_current;
}

void getStatus()
{
  float control_voltage;              //referenced to V_VGND
  float RE_voltage;                   //referenced to power rails
  float WEtoRE_voltage;               //WE voltage referenced to RE
  float WE_current_sense_voltage;     //voltage across current follower sense resistor, ref. to power rails
  float WE_current;                   //compute current into WE
  float WE_current_sense_offset_voltage; //referenced to power rails
  float current_sense_resistance = _currsense_resistors[_currsense_range];
  
  control_voltage = control_DAC.getVoltageOutput() - V_VGND; //shift back from center-rail
  //read signals
  RE_voltage                      = sense_ADC.readSingle(ADC_CHANNEL_VOLTAGE)        - V_VGND;
  WE_current_sense_voltage        = sense_ADC.readSingle(ADC_CHANNEL_CURRENT)        - V_VGND;
  WE_current_sense_offset_voltage = sense_ADC.readSingle(ADC_CHANNEL_CURRENT_OFFSET) - V_VGND;
  //convert to centerline voltage
  WEtoRE_voltage = -RE_voltage;
  //sesning current flows in opposite direction to current flowing into WE
  WE_current     = -WE_current_sense_voltage/current_sense_resistance;
  //format as YAML
  Serial.print(F("#<STATUS>\n"));
  Serial.print(F("---\n"));
  Serial.print(F("control_voltage: "));
  Serial.print(control_voltage, FLOAT_PRECISION_DIGITS);
  Serial.print('\n');
  Serial.print(F("WEtoRE_voltage: "));
  Serial.print(WEtoRE_voltage, FLOAT_PRECISION_DIGITS);
  Serial.print('\n');
  Serial.print(F("WE_current: "));
  Serial.print(WE_current, FLOAT_PRECISION_DIGITS);
  Serial.print('\n');
  Serial.print(F("current_sense_resistance: "));
  Serial.print(current_sense_resistance, FLOAT_PRECISION_DIGITS);
  Serial.print('\n');
  Serial.print(F("WE_current_sense_voltage: "));
  Serial.print(WE_current_sense_voltage, FLOAT_PRECISION_DIGITS);
  Serial.print('\n');
  Serial.print(F("WE_current_sense_offset_voltage: "));
  Serial.print(WE_current_sense_offset_voltage, FLOAT_PRECISION_DIGITS);
  Serial.print('\n');
  Serial.print(F("#</STATUS>\n"));
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
  //Serial.print(F("Tick!\n"));
  _sweep_control_voltage += _sweep_voltage_step;
  noInterrupts();           // disable all interrupts
  //change output voltage
  control_DAC.setVoltageOutput(_sweep_control_voltage + V_VGND); //shift to center-rail
  interrupts();           // enable interrupts
}

void sweepSampleCallback(){
  float RE_voltage;               //referenced to power rails
  float WE_current_sense_voltage; //voltage across current follower sense resistor, ref. to power rails
  
  //sampling starts, do not interrupt for tighter time correlation
  noInterrupts();           // disable all interrupts
  //read signals
  RE_voltage               = sense_ADC.readSingle(ADC_CHANNEL_VOLTAGE) - V_VGND;
  WE_current_sense_voltage = sense_ADC.readSingle(ADC_CHANNEL_CURRENT) - V_VGND;
  interrupts();           // enable interrupts
  //sampling stops, do calculations

  float WEtoRE_voltage;           //WE voltage referenced to RE
  float WE_current;               //compute current into WE
  float current_sense_resistance = _currsense_resistors[_currsense_range];

  //convert to centerline voltage and correct for inversion
  WEtoRE_voltage = - RE_voltage;
  WE_current     = - WE_current_sense_voltage/current_sense_resistance;
  
  //now take care of autoranging
  if (_currsense_auto == true){
    //--------------------------------------------------------------------------
    while (true){
      //out of range upper range
      if (abs(WE_current) > _currsense_autotransitions[_currsense_range]){
        if (_currsense_range > CURRSENSE_RANGE_MIN){
          switchCurrentSenseRange(_currsense_range - 1);
          Serial.print(F("#<AUTORANGE value = "));
          Serial.print(_currsense_range);
          Serial.print(F("/>\n"));
          delay(100);
        } else{ break;}
      }
      //out of lower range
      else if (abs(WE_current) < _currsense_autotransitions[_currsense_range + 1]){
        if (_currsense_range < CURRSENSE_RANGE_MAX){
          switchCurrentSenseRange(_currsense_range + 1);
          Serial.print(F("#<AUTORANGE value = "));
          Serial.print(_currsense_range);
          Serial.print(F("/>\n"));
          delay(100);
        } else{ break;}
      }
      //we are in range
      else{ break;}
      //resample
      noInterrupts(); // disable all interrupts
      RE_voltage               = sense_ADC.readSingle(ADC_CHANNEL_VOLTAGE);
      WE_current_sense_voltage = sense_ADC.readSingle(ADC_CHANNEL_CURRENT);
      interrupts();   // enable interrupts
      current_sense_resistance = _currsense_resistors[_currsense_range];
      WEtoRE_voltage = -(RE_voltage - V_VGND);
      WE_current     = -(WE_current_sense_voltage - V_VGND)/current_sense_resistance;
      //getStatus();
    }
  }
  //format as CSV
  Serial.print(_sweep_control_voltage, FLOAT_PRECISION_DIGITS);
  Serial.print(F(","));
  Serial.print(WEtoRE_voltage, FLOAT_PRECISION_DIGITS);
  Serial.print(F(","));
  Serial.print(WE_current, FLOAT_PRECISION_DIGITS);
  Serial.print(F("\n"));
}

void doSweep(){
  _sweep_control_voltage = _sweep_v_start; //referenced to V_VGND
  _sweep_voltage_step    = _sweep_v_rate*1e-6*SWEEP_UPDATE_PERIOD;
 
  Serial.print(F("#<VSWEEP>\n"));
  Serial.print(F("#<METADATA>\n"));
  Serial.print(F("#start_voltage: "));
  Serial.print(_sweep_v_start, FLOAT_PRECISION_DIGITS);
  Serial.print(F("\n"));
  Serial.print(F("#end_voltage: "));
  Serial.print(_sweep_v_end, FLOAT_PRECISION_DIGITS);
  Serial.print(F("\n"));
  Serial.print(F("#voltage_ramp_rate: "));
  Serial.print(_sweep_v_rate, FLOAT_PRECISION_DIGITS);
  Serial.print(F("\n"));
  Serial.print(F("#sample_rate: "));
  Serial.print(_sweep_samp_rate, FLOAT_PRECISION_DIGITS);
  Serial.print(F("\n"));
  Serial.print(F("#update_period: "));
  Serial.print(1e-6*SWEEP_UPDATE_PERIOD, FLOAT_PRECISION_DIGITS);
  Serial.print(F("\n"));
  Serial.print(F("#voltage_step: "));
  Serial.print(_sweep_voltage_step, FLOAT_PRECISION_DIGITS);
  Serial.print(F("\n"));
  Serial.print(F("#</METADATA>\n"));
  Serial.print(F("#<COLUMNS>control_voltage,WEtoRE_voltage,currentWE_in</COLUMNS>\n"));
  Serial.print(F("#<CSV_DATA>\n"));
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
  Serial.print(F("#</CSV_DATA>\n"));
  Serial.print(F("#</VSWEEP>\n"));
  Timer1.detachInterrupt();
}

//------------------------------------------------------------------------------
//COMMAND HANDLER FUNCTIONS - called by the SCmd dispatcher

void getStatusCommand(){
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    Serial.println(F("### Error: STATUS? requires 0 arguments ###"));
  }
  else
  {
    getStatus();
  }
}

void getCellVoltageCommand(){
  float RE_voltage;               //referenced to power rails
  float WEtoRE_voltage;           //WE voltage referenced to RE
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    Serial.println(F("### Error: VCELL? requires 0 arguments ###"));
  }
  else
  {
    //read signal
    RE_voltage     = sense_ADC.readSingle(ADC_CHANNEL_VOLTAGE);
    //convert to centerline voltage
    WEtoRE_voltage = -(RE_voltage - V_VGND);
    //print out value
    Serial.print(WEtoRE_voltage, FLOAT_PRECISION_DIGITS);
    Serial.print('\n');
  }
}

void getCellCurrentCommand(){
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    Serial.println(F("### Error: ICELL? requires 0 arguments ###"));
  }
  else
  {
    float WE_current = measureCellCurrent();
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
      Serial.print(F("### Error: VCTRL must have ("));
      Serial.print(V_MIN,3);
      Serial.print(F(" <= control_voltage <= "));
      Serial.print(V_MAX,3);
      Serial.print(F(") ###\n"));
      return;
    }
    control_DAC.setVoltageOutput(control_voltage + V_VGND); //shift to center-rail
  }
  else
  {
    Serial.println(F("### Error: VCTRL requires 1 argument (float control_voltage) ###"));
  }
}

void setCurrentRangeLevelCommand(){
  int range_index;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    range_index = atoi(arg);
    if (range_index >= CURRSENSE_RANGE_MIN && range_index <= CURRSENSE_RANGE_MAX)
    {
      switchCurrentSenseRange(range_index);
    }
    else
    {
      Serial.print(F("### Error: IRANGE.LEVEL must have ("));
      Serial.print(CURRSENSE_RANGE_MIN);
      Serial.print(F(" <= range_index <= "));
      Serial.print(CURRSENSE_RANGE_MAX);
      Serial.print(F(") ###\n"));
      return;
    }
  }
  else
  {
    Serial.println(F("### Error: IRANGE.LEVEL requires 1 argument (int range_index) ###"));
  }
}

void setCurrentRangeAutoCommand(){
  int range_index;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    if (strcmp("ON", arg) == 0)
    {
      _currsense_auto = true;
    }
    else if (strcmp("OFF", arg) == 0)
    {
      _currsense_auto = false;
    }
    else
    {
      Serial.print(F("### Error: IRANGE.AUTO 'state' argument must be 'ON' or 'OFF'"));
      Serial.print(CURRSENSE_RANGE_MIN);
      Serial.print(F(" <= range_index <= "));
      Serial.print(CURRSENSE_RANGE_MAX);
      Serial.print(F(") ###\n"));
      return;
    }
  }
  else
  {
    Serial.println(F("### Error: IRANGE.AUTO requires 1 argument (str state) ###"));
  }
}




//------------------------------------------------------------------------------
//VSWEEP commands

void doSweepCommand(){
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    Serial.println(F("### Error: VSWEEP requires 0 arguments ###"));
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
      Serial.print(F("### Error: VSWEEP.START must have ("));
      Serial.print(V_MIN,3);
      Serial.print(F(" <= v_start <= "));
      Serial.print(V_MAX,3);
      Serial.print(F("), got:"));
      Serial.print(v_start,3);
      Serial.print(F(" ###\n"));
      return;
    }
    _sweep_v_start = v_start;
  }
  else
  {
    Serial.println(F("### Error: VSWEEP.START requires 1 argument (float v_start) ###"));
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
      Serial.print(F("### Error: VSWEEP.END must have ("));
      Serial.print(V_MIN,3);
      Serial.print(F(" <= v_end <= "));
      Serial.print(V_MAX,3);
      Serial.print(F(") ###\n"));
      return;
    }
    _sweep_v_end = v_end;
  }
  else
  {
    Serial.println(F("### Error: VSWEEP.END requires 1 argument (float v_end) ###"));
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
      Serial.print(F("### Error: VSWEEP.RAMP must have ("));
      Serial.print(V_MIN,3);
      Serial.print(F(" <= v_rate <= "));
      Serial.print(V_MAX,3);
      Serial.print(F(") ###\n"));
      return;
    }
    _sweep_v_rate = v_rate;
  }
  else
  {
    Serial.println(F("### Error: VSWEEP.RAMP requires 1 argument (float v_rate) ###"));
  }
}

void setSweepSampleRateCommand(){
  float samp_rate;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL)
  {
    samp_rate = atof(arg);
    if (samp_rate >= SAMPRATE_MIN && samp_rate <= SAMPRATE_MAX)
    {
      _sweep_samp_rate = samp_rate;
      return;
    }
    else
    {
      Serial.print(F("### Error: VSWEEP.SAMPLE must have ("));
      Serial.print(SAMPRATE_MIN,3);
      Serial.print(F(" <= samp_rate <= "));
      Serial.print(SAMPRATE_MAX,3);
      Serial.print(F(") ###\n"));
      Serial.print(samp_rate);
      return;
    }
    
  }
  else
  {
    Serial.println(F("### Error: VSWEEP.SAMPLE requires 1 argument (float samp_rate) ###"));
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
    Serial.println(F("### Error: VSWEEP.CYCLES requires 1 argument (int cycles) ###"));
  }
}


//------------------------------------------------------------------------------

// Unrecognized command
void unrecognizedCommand(const char* command)
{
  Serial.print(F("### Error: command '"));
  Serial.print(command);
  Serial.print(F("' not recognized ###\n"));
}
