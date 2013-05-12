 /* Jan_8_ASV_CV_For_GUI
  Pulsed stripping voltammetry and cyclic voltammetry sketch 
   for processing GUI 
 Based on BHickman work --Version 3; got the initial delay working
 ****************************************/

void setup_run (void);
void conversions (void);
void stripping_volt (void);

/**********USER DEFINED VARIABLES*******************/
int Vopen = 0;                  // open circuit voltage, no current passes 
float Vinit = 0;                    // initial voltage, 
//  To oxidize materials remaining on the working electrode 
int Vplat = 0;                 // plating voltage                  
float Vfnl = 0;                   // scan final duty cycle                  
int pulse_volt = 0;               // scan final duty cycle 
//int electrode_clean = 5000;
int plating_delay = 2000;         // plating delay
long initial_delay = 2000;           // JSS initial delay time (mseconds)
long sr = 0;                            // number of pwm cycles at a one pulse delay
// entered as scan rate in mv/s
int pwm_step = 3;           // pwm increment for step
int pgm = 0;

/*********NON-USER VARIABLES*********************/
int place[4]={
  1000,100,10,1};   // serial read conversions
int incomingByte[4] = {
  0,0,0,0};           // serial read variable
unsigned int duty_cyc;         // duty cycle variable
long initial_ms = 0;                  // JSS initial delay time (mseconds)
int plating_ms = 1000;               // JSS pre concentration time (seconds)
int pcon = 0;                          //
int val = 0;                             // serial read variable
float inVolt = 0;                 // voltage read
float Iread1 = 0;                 // hight pulse current read 
float Iread2 = 0;                 // low pulse curent read   
float Iread = 0;                 // Iread1 - Iread2
float LDO = 1.794;    //measured low dropout oscillator voltage in V 
#define  pwm_pin  P2_1            // Pin 2.1
#define  pulse_pin  P2_0         // Pin 2.0, changed, Jan29 JSS
#define  Iread_pin  A4           // Pin 1.4   
#define  Vread_pin  A5             //Pin 1.5
#define  stir_pin  P2_4            // Pin 2.4


/**********************************************/
void setup() {

  pinMode (pwm_pin,OUTPUT);      // set pin 2.1 for output   
  pinMode (pulse_pin,OUTPUT);      // set pulse pin as output
  pinMode (Vread_pin,INPUT);
  pinMode (Iread_pin,INPUT);
  //pinMode (Offset_read_pin,INPUT); 
  pinMode (stir_pin,OUTPUT);      /// set pin 2.4 for output
  analogResolution(1023);         // divide the full duty cycle into 1024 steps
  analogFrequency(5000);          // set the full duty cycle to 0.2 ms
  Serial.begin(9600);             // begin serial comm. at 9600 baud

}

void loop() {

  digitalWrite(pulse_pin,LOW);
  digitalWrite(stir_pin,LOW);
  setup_run();
  conversions ();
  stripping_volt ();

}

/////////////////////////////// stripping volttammetry /////////

void stripping_volt (){

  if(pgm==1){
    initial_delay = initial_delay*1000;   // convert initial delay ms to sec
    //long initial_delay = 60000;  // added mar 8, 13 JSS
    delay(1);
    // Serial.println("press any number 1-9 to begin");
    while (Serial.read() >= 0);            // clear serial available
    while (Serial.available()<= 0) {
    }
    while (Serial.available() > 0){
      // Serial.println("Start initial delay"); 

    //  analogWrite(pwm_pin,1000);   //cut 3-7-13-JSS
      //Serial.println("Electrode cleaning delay (5 sec)");
     // delay(electrode_clean);                   // set volt to vfnl to clean electrod  cut 3-7-13-JSS

      analogWrite(pwm_pin,Vinit);               // set voltage to Vinit
      //Serial.println("plaiting time");
      digitalWrite(stir_pin,HIGH);
      delay(initial_delay);                        // stay at Vinit for initial_delay in sec 
      digitalWrite(stir_pin,LOW); 

      Vplat = Vinit;                             // BH set plating voltage to initial voltage
      analogWrite(pwm_pin,Vplat);               // set voltage for concentration step
      // Serial.println("Quite time (2 sec)");
      delay(plating_delay);                        // stay at plating voltage for plating_delay in sec  


      for (int duty_cyc = Vplat; duty_cyc <= Vfnl; duty_cyc += pwm_step){
        inVolt = 0;                 // voltage read
        Iread1 = 0;                 // hight pulse current read 
        Iread2 = 0;                 // low pulse curent read    
        // increment the step voltage every iteration
        if(duty_cyc == 255){
          duty_cyc = duty_cyc + 1;
        }
        analogWrite(pwm_pin,duty_cyc);
        digitalWrite(pulse_pin,LOW);              // set pulse pin to low
        delay(sr);
        for (int i =0; i<=15; ++i){
          Iread2 += analogRead(Iread_pin);
        }
        for (int i =0; i<=3; ++i){
          inVolt += analogRead(Vread_pin);//inVolt += analogRead(Vread_pin);
        }
        // inVolt = analogRead(A0)*0.003515625;                    // 10 bit A to D conversion
        inVolt = LDO-((inVolt/4)*0.003474609);    //LDO is V
        Iread2 = (Iread2/16)*0.003474609;
        Serial.print(inVolt,4);
        Serial.print('\t');
        Serial.print(Iread2,4);


        digitalWrite(pulse_pin,HIGH);                // set pulse pin to high
        delay(sr);
        for (int i =0; i<=15; ++i){
          Iread1 += analogRead(Iread_pin);
        }
        Iread1 = (Iread1/16)*0.003474609;
        Serial.print('\t');
        Serial.println(Iread1,4);
      }
      delay(10);
      Serial.println('*');
      delay(10);
      while (Serial.read() >= 0);                  // clear serial available  
    }
  }
  if(pgm==2){   ///cyclic voltammetry//////////////////////////////////////////////////
    if(Vinit> Vfnl){
      delay(1);
      // Serial.println("press any number 1-9 to begin");
      while (Serial.read() >= 0);            // clear serial available
      while (Serial.available()<= 0) {
      }
      while (Serial.available() > 0){
        // Serial.println("Start initial delay"); 

      //  analogWrite(pwm_pin,1000);
        //Serial.println("Electrode cleaning delay (5 sec)");
      //  delay(electrode_clean);                   // set volt to vfnl to clean electrod
        analogWrite(pwm_pin,Vinit);               // set voltage to Vinit
      //  Vplat = Vinit;                             // BH set plating voltage to initial voltage
        // Serial.println("Quite time (2 sec)");
     delay(initial_delay);                   // set volt to vfnl to clean electrod
   
        for (int duty_cyc = Vinit; duty_cyc >= Vfnl; --duty_cyc ){
          inVolt = 0;                 // voltage read
          Iread1 = 0;                 // hight pulse current read 
          Iread2 = 0;                 // low pulse curent read    
          // increment the step voltage every iteration
          if(duty_cyc == 255){
            duty_cyc = duty_cyc - 1;
          }
          analogWrite(pwm_pin,duty_cyc);
          delay(sr);
          for (int i =0; i<=15; ++i){
            Iread2 += analogRead(Iread_pin);
          }
          for (int i =0; i<=3; ++i){
            inVolt += analogRead(Vread_pin);//inVolt += analogRead(Vread_pin);
          }
          // inVolt = analogRead(A0)*0.003515625;                    // 10 bit A to D conversion
          inVolt = LDO-((inVolt/4)*0.003474609);
          Iread2 = (Iread2/16)*0.003474609;
          Serial.print(inVolt,4);
          Serial.print('\t');
          Serial.println(Iread2,4);
        }
        for (int duty_cyc = Vfnl; duty_cyc <=Vinit; ++duty_cyc ){
          inVolt = 0;                 // voltage read
          Iread1 = 0;                 // hight pulse current read 
          Iread2 = 0;                 // low pulse curent read    
          // increment the step voltage every iteration
          if(duty_cyc == 255){
            duty_cyc = duty_cyc + 1;
          }
          analogWrite(pwm_pin,duty_cyc);
          delay(sr);
          for (int i =0; i<=15; ++i){
            Iread2 += analogRead(Iread_pin);
          }
          for (int i =0; i<=3; ++i){
            inVolt += analogRead(Vread_pin);//inVolt += analogRead(Vread_pin);
          }
          // inVolt = analogRead(A0)*0.003515625;                    // 10 bit A to D conversion
          inVolt = LDO-((inVolt/4)*0.003474609);
          Iread2 = (Iread2/16)*0.003474609;
          Serial.print(inVolt,4);
          Serial.print('\t');
          Serial.println(Iread2,4);
        }
        delay(10);
        Serial.println('*');
        delay(10);
        while (Serial.read() >= 0);                  // clear serial available  
      }
    }
    else{
      delay(1);
      // Serial.println("press any number 1-9 to begin");
      while (Serial.read() >= 0);            // clear serial available
      while (Serial.available()<= 0) {
      }
      while (Serial.available() > 0){
        // Serial.println("Start initial delay"); 

      //  analogWrite(pwm_pin,1000); //cut 3-7-13-JSS
        //Serial.println("Electrode cleaning delay (5 sec)");
    //    delay(electrode_clean);      // cut 3-7-13-JSS     set volt to vfnl to clean electrod
        analogWrite(pwm_pin,Vinit);               // set voltage to Vinit
        Vplat = Vinit;                             // BH set plating voltage to initial voltage
        // Serial.println("Quite time (2 sec)");

        for (int duty_cyc = Vinit; duty_cyc <= Vfnl; ++duty_cyc ){
          inVolt = 0;                 // voltage read
          Iread1 = 0;                 // hight pulse current read 
          Iread2 = 0;                 // low pulse curent read    
          // increment the step voltage every iteration
          if(duty_cyc == 255){
            duty_cyc = duty_cyc + 1;
          }
          analogWrite(pwm_pin,duty_cyc);
          delay(sr);
          for (int i =0; i<=15; ++i){
            Iread2 += analogRead(Iread_pin);
          }
          for (int i =0; i<=3; ++i){
            inVolt += analogRead(Vread_pin);//inVolt += analogRead(Vread_pin);
          }
          // inVolt = analogRead(A0)*0.003515625;                    // 10 bit A to D conversion
          inVolt = LDO-((inVolt/4)*0.003474609);
          Iread2 = (Iread2/16)*0.003474609;
          Serial.print(inVolt,4);
          Serial.print('\t');
          Serial.println(Iread2,4);
        }
        for (int duty_cyc = Vfnl; duty_cyc >=Vinit; --duty_cyc ){
          inVolt = 0;                 // voltage read
          Iread1 = 0;                 // hight pulse current read 
          Iread2 = 0;                 // low pulse curent read    
          // increment the step voltage every iteration
          if(duty_cyc == 255){
            duty_cyc = duty_cyc - 1;
          }
          analogWrite(pwm_pin,duty_cyc);
          delay(sr);
          for (int i =0; i<=15; ++i){
            Iread2 += analogRead(Iread_pin);
          }
          for (int i =0; i<=3; ++i){
            inVolt += analogRead(Vread_pin);//inVolt += analogRead(Vread_pin);
          }
          // inVolt = analogRead(A0)*0.003515625;                    // 10 bit A to D conversion
          inVolt = LDO-((inVolt/4)*0.003474609);
          Iread2 = (Iread2/16)*0.003474609;
          Serial.print(inVolt,4);
          Serial.print('\t');
          Serial.println(Iread2,4);
        }
        delay(10);
        Serial.println('*');
        delay(10);
        while (Serial.read() >= 0);                  // clear serial available  
      }
    }
  }
  else{
  }
}

///////////////////////////////////////// setup run ////////////////////////////
void setup_run(){

  int n=0;
  Vinit = 0;
  Vfnl = 0;
  sr = 0;
  initial_delay = 0;
  pgm = 0;


  //////////start voltage/////////////////////////////////
  Serial.println("Starting Voltage (mV-1800mV)");
  delayMicroseconds(300); 
  int Vt = 0;
  n = 0;
  while (Serial.read() >= 0);       // clear serial available   
  while (Serial.available()<= 0) {
  }   //does this do anything?
  while (Serial.available() > 0){
    incomingByte[n] = Serial.read()-48;            // read incoming Byte and onvert from ascii to decimal
    delay(2);
    ++n;          
  }
  for(int n=0;n<=3;++n){
    Vt = Vt + (place[n]*(incomingByte[n]));        // convert from ascii to decimal 
  }
  Vinit=Vt;
  Serial.println(Vinit);  

  /////////////////////ending voltage/////////////////////
  Serial.println("Ending Voltage (mV-1800mV)");  
  delayMicroseconds(300);   
  int Vf = 0;
  n=0;   
  //  while (Serial.read() >= 0); // clear serail available
  while (Serial.available()<= 0) {
  }
  while (Serial.available() > 0){      
    incomingByte[n] = Serial.read()-48;
    delay(2);
    ++n;
  }
  for(int n=0;n<=3;++n){
    Vf = Vf + (place[n]*(incomingByte[n])); 
  }
  Vfnl = Vf;
  Serial.println(Vfnl);  

  //////////////scan rate/////////////////////////////////
  Serial.println("Scan Rate in mV/sec (sec)");
  int wtf = 0; 
  n=1;
  delayMicroseconds(300);  
  //  while (Serial.read() >= 0);           // clear serial available   
  while (Serial.available()<= 0) {
  }
  while (Serial.available() > 0){   
    incomingByte[n] = Serial.read()-48;
    delay(2);
    ++n;
  }
  for(int n=1;n<=3;++n){
    wtf = wtf + (place[n]*(incomingByte[n]));
  } 
  sr=wtf;    
  Serial.println(sr);

  ////////////////pre-conc time//////////////////////////////////////
  Serial.println("Pre-concentration time (sec)");
  int pcon = 0; 
  //n=0;    //changed JSS  3-8-13, didnt work
   n=1;
  delayMicroseconds(300);  
  //  while (Serial.read() >= 0); // clear serial available   
  while (Serial.available()<= 0) {
  }
  while (Serial.available() > 0){  
    incomingByte[n] = Serial.read()-48;
    delay(2);
    ++n;
  }
  for(int n=1;n<=3;++n){
    pcon = pcon + (place[n]*(incomingByte[n]));
  } 
  initial_delay = pcon;   
  Serial.println(initial_delay);

  ////////////////mode//////////////////////////////////////  
  Serial.println("Mode (0:ASV, 1:CV)");
  int mod = 0; 
  n=0;
  delayMicroseconds(300);  
  // while (Serial.read() >= 0); // clear serial available   
  while (Serial.available()<= 0) {
  }
  while (Serial.available() > 0){  
    incomingByte[n] = Serial.read()-48;
  }
  pgm = incomingByte[n];
  Serial.println(pgm);

  Serial.println('&');
}



//////////////////////////////////// conversions ///////////////////////////////  
void conversions (){
  int corr = (LDO * 1000) - 1852;    //correction fof differences in LDO voltages
                                      //corrections relative to value in GUI
  Vinit = (((Vinit - corr)/3558)*1024);   // convert input voltage to pwm value  Vinit = (Vinit/36)*10.24;
  delay(1);
  Vfnl = (((Vfnl - corr)/3558)*1024);  //Vfnl = (Vfnl/31.7)*10.24; 5200
  delay(1);
  if(pgm==1){
    sr = (1800/sr)*pwm_step;
    delay(1);
  }
  if(pgm==2){
    sr = 1800/sr;
    delay(1);
  }
}




