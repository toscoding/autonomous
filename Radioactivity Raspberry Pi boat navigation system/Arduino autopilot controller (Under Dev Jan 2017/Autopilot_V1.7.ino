

String datestring = "Olly Epsom Feb 2017 ";
String versionstring = "Software Version 1.7";

/*
  03 Feb 2017
  Includes LCD display driver.
  Includes Tilt compensated compass reading
  Includes power monitoring and display
  Includes Warnings and Alarms
  Includes LED indicatiors
  Includes inhibit of alarms for the tacking and manual drive functions
  Includes minor code tidy ups
  Includes my ned re-setting integral PID system
  Includes advanced button driver
  Includes resume function
  Includes dim-whilst-live
  Includes running gain ajustment
  Includes Bluetooth Connectivity
*/
// ********************************************************************************

/*******************************************************************************
  IO DEFINITION
*******************************************************************************/

//-----( Import needed libraries )-----//
#include <Wire.h>

// Get the LCD I2C Library here:
// https://bitbucket.org/fmalpartida/new-liquidcrystal/downloads
#include <LiquidCrystal_I2C.h>

//Info for tilt compensated compass
#define CMPS11_ADDRESS 0x60  // Address of CMPS11 shifted right one bit for arduino wire library
#define ANGLE_8  1           // Register to read 8bit angle from
unsigned char high_byte, low_byte, angle8;
char pitch, roll;
unsigned int angle16;
int filterbearing;            //Smoothed bearing
int coursedemand;             //Demanded course
int resumedemand;             //Stored demand, called when "Resume" is pressed
int headingerror;             //Heading error
int abserror;                 //ABS error, used for sign correction
const int motordirection = -1;      //Change this if the motor is giving positive rather than negative feedback (If wires are connected properly this should be -1 so that the demand is the opposite direction to the error.)
const int minmotorspeed = 40;       //Do not turn motor on until a power of at least this value is demanded.
const int deadband = 2;             //Minimum error before motor moves
boolean dirselect = true;           //Used to set the direction when ram movement selected
int testprog = 3;                       //Inhibit motor movements in this ptorgram mode - switch to 3 to de-inhibit


// Set PID controller values

float Pgain = 1;               //Proportional gain for the system units of output (0-255) per degree of error
float Igain = 1;               //Integral gain for the system in units of output (0-255) per (Error in degreres * time in seconds) - Please make it an even number
float Dgain = 1;               //Differential gain for the system units of output (0-255) per (Delta Error/second) - Please make it an even number
int Ogain = 10;               //User definable gain setting which is altered by pressing button 5
int Mgain = 20;               //Maximum permitted value of Ogain
int Again = 2;                //Steps to ajust Ogain by
int tmr;                      //General purpose ticker variable
int SampleTime = 500;         //Time interval for PID in Miliseconds - The above values are then tuned


int outMax = 100;             //Max integral component out of 255
int outMin = -100;            //Min integral component out of -255




//Set variables for LDD display

// set the LCD address to 0x27 for a 20 chars 4 line display //
LiquidCrystal_I2C lcd(0x27, 2, 1, 0, 4, 5, 6, 7, 3, POSITIVE);  // Set the LCD I2C address

static int backlightpin = 3;       //LED connected to PWM out pin 3 (If jumper on board disconnected.)
int brightness = 255;              //Initial brightness of backlight for LCD and program LED
static int brightchange = 20;      //Interval for changing the brighness
int powerpercent = 0;              //Percentage value of motor power

//Set PWM pins and data for motor driver //
const int pinPwm = 11;      // Motor drive PWM is connected to pin 11.
const int pinDir = 13;      // Motor direction is connected to pin 13.
static int iSpeed = 0;      // Initial speed of the motor.

//Set self-monitoring pins for voltage and current checking.  Note - ensure the potential dividers are fitted as system can not read 12V!
const int voltagepin = 1;         //Analog input for voltage monitoring is pin A1
const int currentpin = 2;         //Current sensing pin is A2
const float curris = 0.4;         //Value of the current sensing resistor in ohms
const float voltagecal = .0152;   //One bit on the analoug read pin is mapped to this Mv reading
int voltread;               //variable read for voltage term
int curread;                //variable read for current reading


float voltdis;              //Calculated voltage
float curdis;               //Calculated current
int poweruse;               //Calculated power draw
int lastpoweruse = 100;         //Used to prevent jumpy displays - initial high setting means values display as I have set them to only update on substantial changes

// Set filtering values

const int headlength = 5; //grab this number of values for heading



//Set info for program mode and error detection
int prgmode = 0;            //Initial mode = mode zero, i,e autopilot off.
int nxtmode = 0;            //Next program mode
int maxmode = 2;            //Numper of programs to scroll through
int lastprg = 0;            //Last program, used for the resume function.  Set as 0 at start and used to get the first course (Default programme at start)

//Define possible user messages
int dismsg = 0;           //Display message number 0 from the array
const char*usrmsg[] = {" F-A-B ", "Nprg 0", "Nprg 1 ", "Nprg 2 ", "Alt Sb ", "Alt Pt ", "W-Low V", "W-Hdg  ", "A-Hi C ", "A-Low V", "A-Hdg  "};

//Define input and output relay pins for audible alarm and warning LEDs and relay/switch inputs - You may need to alter these to suit your own paticular relay board.
const int alarmpin = 4;         //Alarm pin is 4
const int LED1 = 6;             //LED1 pin is 6

const int buttonpins[] = {2, 9, 10, 12, 14, 17}; //Array of pin numbers for the buttons 2,6,10,12,14,17, Note pins 14 and 17 are the analog input pins alternativly labled A0 and A3
const int buttons = 6;                      //There are 6 user buttons
int pinscan;                          //Integer used as a for loop for scanning the input buttons
int buttonpress = 0;                  //This becomes a number from 1 to 6 if a button is pressed

int corinput = 0;                     //Triggered to -1 or +1 if button 1 or 2 pressed, and + or - tack angle if 5 or 6 pressed
const int tackangle = 100;            //Angle to tack through if buttons 5 or 6 pressed in mode
boolean manflag = false;              //Flag for manual overide is not engaged
boolean manmove = false;              //If true overpowers iSpeed to max
const int longhold = 1000;             //Duration in miliseconds needed before a button is considered held for  "Long" time


//Define flashing and warning timers
unsigned long StartTime = millis();
unsigned long CurrentTime = millis();
unsigned long ElapsedTime = CurrentTime - StartTime;
int flashdur = 500;                     //Flash interval
boolean alarm = false;                  //Alarm is "Off"
boolean warning = false;                //LED1 is "Off"
boolean warningrst = true;              //goes false during warning flashing phase when autopilot still active

//Define warning and alarm triggers
const float warnvoltage = 11.7;
const int warnhdg = 20;

const float alarmcurrent = 5;
const float alarmvoltage = 11.5;
const int alarmhdg = 30;
boolean inhibithdg = false;                 //Flag used to inhibit heading alarm

//Define Bluetooth communications protocols
int bluesignal = 0;                   //Bluetooth signal name











/*******************************************************************************
   FUNCTIONS
 *******************************************************************************/

void setup() {
  // Initialize the PWM and DIR pins as digital outputs.
  pinMode(pinPwm, OUTPUT);
  pinMode(pinDir, OUTPUT);
  pinMode(alarmpin, OUTPUT);
  pinMode(LED1, OUTPUT);
  SetTunings();                 //Tune PID gains for the relevant sample time

  //Initiate the user input pins
  for (pinscan = 0; pinscan < buttons; pinscan++)  {
    pinMode(buttonpins[pinscan], INPUT_PULLUP);
  }


  pinMode(backlightpin, OUTPUT);          // sets the pin as output
  analogWrite(backlightpin, brightness);  //Sets the initial backlight brightness
  Wire.begin();                           //Start serial interface for compass
  lcd.begin(20, 4);                       // initialize the lcd for 20 chars 4 lines, turn on backlight


  //-------- Write Introduction on the display ------------------
  digitalWrite(alarmpin, HIGH);
  digitalWrite(LED1, HIGH);
  lcd.setCursor(0, 0); //Start at character 4 on line 0
  lcd.print("RADIOACTIVITY");
  delay(300);
  digitalWrite(alarmpin, LOW);
  digitalWrite(LED1, LOW);
  lcd.setCursor(0, 1);
  lcd.print("Autopilot control");
  delay(300);
  digitalWrite(alarmpin, HIGH);
  digitalWrite(LED1, HIGH);
  lcd.setCursor(0, 2);
  lcd.print(datestring);
  delay(300);
  digitalWrite(alarmpin, LOW);
  digitalWrite(LED1, LOW);
  lcd.setCursor(0, 3);
  lcd.print(versionstring);
  delay(2000);



  lcd.setCursor(0, 0);
  lcd.print("Msg=       Program=");
  lcd.setCursor(0, 1);
  lcd.print("Cts=     D Hdg=    D");
  lcd.setCursor(0, 2);
  lcd.print("Mot=     % Err=    D");
  lcd.setCursor(0, 3);
  lcd.print("Amp=     A Vlt=    V");

  Serial.begin(9600); // Default communication rate of the Bluetooth module

}/*--(end setup )---*/












// The loop routine runs over and over again forever.
void loop() {
  CurrentTime = millis();

  //Calculate filtered bearing
  filterbearing = bearinggrab(headlength);

  //set default course demand if system is in mode 0
  if (prgmode == 0) {
    coursedemand = filterbearing;
    if (lastprg == 0) { //For the first time the system is turned on, the resume demand will be the course demand, otherwise it will be the last selected course
      resumedemand = coursedemand;
      lastprg = 1;    //Set the default program to 1 the first time the autohelm is started.
    }
  }


  // Calculate heading error and motor demand, provided autopilot is active.

  headingerror = CompassError(filterbearing, coursedemand);
  if (prgmode > 0) {
    iSpeed = PID(headingerror, CurrentTime);      //Calculate output to motor to correct heading error
  }
  else {
    iSpeed = 0;
  }


  // reset inhibit heading if error has dropped below warning threshold (For example following a tack or a manual intervention which has raised the inhibit heading flag)
  if (inhibithdg == true) {
    if ((abs(headingerror) < warnhdg) || (prgmode == 0))  {
      inhibithdg = false;
      dismsg = 0;
    }
  }


  bluesignal = bluescan(curdis);               //This returns the Bluetooth reading if applicable
  if (prgmode == 2) {
    iSpeed = bluesignal;
  }

  //Set motor direction pin
  if (manmove == false) {
    if (iSpeed >= 0) {
      dirselect = false;
    }
    else {
      dirselect = true;
    }

    //Bound motor speed between permitted minumum and maximum

    iSpeed = abs(iSpeed);
    iSpeed = constrain (iSpeed, 0, 255);                      //Constrain iSpeed so it is never more than 255 (which is 100%)

    // Constain iSpeed the other way, so if its less than the minimum motor speed, iSpeed will be set to zero
    if (iSpeed < minmotorspeed) {
      iSpeed = 0;
    }
  }
  else {
    iSpeed = 255; //If manual demand selected
  }

  powerpercent = iSpeed / 2.55;  //Percentage motor power for display, defaults to a positive value

  if (dirselect == true) {       //Inverts percentage if motor reversing
    powerpercent *= -1;
  }


  // Set motor to work
  if (prgmode != testprog) { //Only activate the motor in PWM mode if program 0 or 2 selected (This allows mode 1 for testing, remove later)
    analogWrite(pinPwm, iSpeed);
    digitalWrite(pinDir, dirselect);
  }


  //Measure and calculate power demands

  voltread = analogRead(voltagepin);   // read the input pin for voltage
  curread = analogRead(currentpin);   // read the input pin for current
  voltdis = voltread * voltagecal;
  curdis = ((voltread - curread) * voltagecal) / curris;
  poweruse = voltdis * curdis;

  //User interface control

  buttonpress = buttonscan();            //This returns a number from 0 to 12 which represents the status of the buttons.  System is not capable of identifing if more than one button is pressed, it simply takes the highest one and uses that.


  //Beep if button pressed
  if ((buttonpress > 0) && (manflag == false)) {
    digitalWrite(alarmpin, HIGH);
    delay(50);
    digitalWrite(alarmpin, LOW);
    lcd.setCursor(4, 0);
  }

  //Mode scrolling
  if (buttonpress == 4) {
    if (nxtmode == maxmode) {
      nxtmode = 0;
    }
    else {
      nxtmode += 1;
    }
    dismsg = nxtmode + 1;
  }

  //Mode selection and set, reset and resume
  if ((buttonpress == 3) || (buttonpress == 9)) {
    if (buttonpress == 3) {
      //Set program 1 by default if 3 pressed in mode 0 and next mode <2
      if ((prgmode == 0) && (nxtmode < 2)) {
        nxtmode = 1;
      }

      prgmode = nxtmode;
      nxtmode = 0;
      dismsg = 0;

      if (prgmode == 0) {
        analogWrite(pinPwm, 0); //Knock of motor if its moving when mode 0 selected
        lcd.print("Exited");
        digitalWrite(LED1, LOW); //Turn off program selection LED
      }

      if (prgmode > 0) {
        lcd.print("Active");
        resumedemand = coursedemand; //Sets resume demand to current course
        digitalWrite(LED1, HIGH); //Turn on program selection LED
        lastprg = prgmode; // Remember program for resumed function.
      }
    }
    // Resume course and last programme if button 9 is pressed
    else {
      coursedemand = resumedemand;
      lcd.print("Resumed");
      digitalWrite(LED1, HIGH); //Turn on program selection LED
      prgmode = lastprg;  //Turn to last program
      inhibithdg = true;

    }

    //Beep to indicate program selections
    for (tmr = 0; tmr < (prgmode + 1); tmr ++) {
      delay (100);
      digitalWrite(alarmpin, HIGH);
      delay(100);
      digitalWrite(alarmpin, LOW);
    }

    delay(1000);
  }






  //Handle manual overide - Quite complicated hence the code - If in mode 0 buttons 1 and 2 move ram directly.  If in mode >0 and buttons held for a short time they move ram directly but autopilot reengages afterwards, otherwise they ajust the Cts



  // Handle correction of course
  if ((buttonpress == 1) || (buttonpress == 7)) {
    corinput = -1 * motordirection;
    dirselect = false;
    dismsg = 4;

  }


  if ((buttonpress == 2)  || (buttonpress == 8)) {
    corinput = 1 * motordirection;
    dirselect = true;
    dismsg = 5;

  }


  // Set manual movement flags if called for
  if ((buttonpress == 7)  || (buttonpress == 8)) {
    manflag = true;
    manmove = true;
    inhibithdg = true;
    prgmode = 0;
    digitalWrite(LED1, LOW); //Turn off program selection LED


  }

  // Reset manual movement flags if called for
  if ((manflag == true) && (buttonpress != 7) && (buttonpress != 8)) {
    manflag = false;                //Remove manual overide flag
    manmove = false;                //remove speed overide
    analogWrite(pinPwm, 0);         //set motor to off in case it has been "On"
    dismsg = 0;
  }


  //Cycle gains if button 5 pressed
  if (buttonpress == 5) {

    Ogain += Again;

    if (Ogain > Mgain) {
      Ogain = Again;
    }
    lcd.print("Gain=");
    lcd.print(Ogain);
    delay (500);
  }



  // Ajust brightness if button 6 is pressed

  if (buttonpress == 6) {

    brightness += brightchange;

    if (brightness > 255) {
      brightness = 0;
    }
    analogWrite(backlightpin, brightness);  //Sets the new backlight brightness
    delay (10);
  }


  //Up and down by a tack angle (Note because of the button configurations on my remote control 1 and 6 give Stbd turns and 2 and 5 port, which is a bit counter intuitive
  //In mode 0 buttons 5 and 6 ajust the backlight intensity


  if (buttonpress >= 11) {            //If button 11 or 12 pressed, do something
    inhibithdg = true;
    prgmode = 1;

    if (buttonpress == 11) {           //Tack to Port if button 11 is pressed
      corinput = 1 * motordirection * tackangle;
      lcd.print("Tk Pt ");
      delay (1000);
    }

    else {                         //Tack to Stbd if button 12 is pressed
      corinput = -1 * motordirection * tackangle;
      lcd.print("Tk Stb ");
      delay (1000);
    }
  }








  // Adjust coursedemand following manual input from buttons
  if ((prgmode != 0) && (corinput != 0) && (manflag == false)) {
    coursedemand += corinput;

    //Correct if demand is <>0 or 360
    if (coursedemand >= 360) {
      coursedemand -= 360;
    }
    if (coursedemand <= 0) {
      coursedemand += 360;
    }
    corinput = 0;
    resumedemand = coursedemand;
  }




  //Detect and display errors handling section
  if (voltdis < warnvoltage) {
    warning = true;
    dismsg = 6;
    if (voltdis < alarmvoltage) {
      alarm = true;
      dismsg = 9;
    }
  }
  //Note heading error only occurs if autopilot is active
  if (prgmode > 0) {
    if (abs(headingerror) > warnhdg) {
      warning = true;
      dismsg = 7;
      if ((abs(headingerror) > alarmhdg) && (inhibithdg == false)) {
        alarm = true;
        dismsg = 10;
      }
    }
  }

  if (curdis > alarmcurrent) {
    alarm = true;
    dismsg = 8;
  }



  //Handle resetting of alarms and warnings after a given time
  if ((warning == true) || (alarm == true)) {
    if (warningrst == true) {
      if (alarm == true) {
        prgmode = 0;
        analogWrite(pinPwm, 0);         //set motor to off in case it has been "On"
      }
      StartTime = millis();
      warningrst = false;
    }

    CurrentTime = millis();
    ElapsedTime = CurrentTime - StartTime;

    delay (100);
    digitalWrite(LED1, HIGH);
    if (alarm == true) {
      digitalWrite(alarmpin, HIGH);
    }

    delay (100);
    digitalWrite(LED1, LOW);
    if (alarm == true) {
      digitalWrite(alarmpin, LOW);
    }

    if (ElapsedTime > 1000) {

      alarm = false;
      warning = false;
      warningrst = true;
      if (prgmode > 0) {
        digitalWrite(LED1, HIGH);
      }
    }
  }


  //Display infomation on LCD display
  lcd.setCursor(4, 0);
  lcd.print(usrmsg[dismsg]);

  lcd.setCursor(19, 0);
  lcd.print(prgmode);

  lcd.setCursor(4, 1);
  lcd.print("    ");
  lcd.setCursor(4, 1);
  lcd.print(coursedemand);

  lcd.setCursor(15, 1);
  lcd.print("    ");
  lcd.setCursor(15, 1);
  lcd.print(filterbearing);


  lcd.setCursor(4, 2);
  lcd.print("    ");
  lcd.setCursor(4, 2);
  lcd.print(powerpercent);

  lcd.setCursor(15, 2);
  lcd.print("    ");
  lcd.setCursor(15, 2);
  lcd.print(headingerror);

  if (abs(poweruse - lastpoweruse) > 3) {

    lcd.setCursor(4, 3);
    lcd.print("     ");
    lcd.setCursor(4, 3);
    lcd.print(curdis, 2);

    lcd.setCursor(15, 3);
    lcd.print("    ");
    lcd.setCursor(15, 3);
    lcd.print(voltdis, 1);

  }


  delay(50);
}












// **** important subroutines start here ***


//Check and return button status
int buttonscan() {
  int pressed = 0;
  static boolean buttonarray[3][6] = {{false, false, false, false, false, false}, {false, false, false, false, false, false}}; //Array for handing button controls
  static unsigned long buttontime[6];

  // Return from this function is a number from 0 to 12.  0 is no button pressed.  1-6 is the buttons pressed in instantaneous mode.  7-12 is the buttons pressed in "Long" mode.


  //Scan the input buttons
  for (pinscan = 0; pinscan < buttons; pinscan++)  {
    if ((digitalRead(buttonpins[pinscan])) == LOW) {

      if (buttonarray[0][pinscan] == false) {
        //Turn the flag to true and start the clock
        buttonarray[0][pinscan] = true;
        buttontime[pinscan] = CurrentTime;
      }
      else {
        //Calculate the time that the button has remained pressed for and if pressed=pinscan+7, else pressed=pinscan+1
        if  ((CurrentTime - buttontime[pinscan]) >= longhold) {
          buttonarray[1][pinscan] = true;
          pressed = pinscan + 7;

        }
        else {
          buttonarray[1][pinscan] = false;
        }
      }
    }

    else {
      if ((pressed == 0) && (buttonarray[0][pinscan] == true)) {
        if (buttonarray[1][pinscan] == false) {
          pressed = pinscan + 1;
        }
      }
      buttonarray[0][pinscan] = false;
      buttonarray[1][pinscan] = false;
    }
  }

  return pressed;
}



//Check and return button status
int bluescan(float currentcurrent) {
  static float lastcurrent;
  int received = 0;

  if (Serial.available() > 0) { // Checks whether data is comming from the serial port
    received = Serial.read(); // Reads the data from the serial port

    Serial.print (received);


  }

  lastcurrent = currentcurrent;
  return received;
}



















// Grab heading out of compass and give it an inital smooth
int bearinggrab(int cycles) {
  int smooth = 0;
  int raw = 0;
  int vals = 0;

  for (int i = 1; i <= cycles; i++) {

    Wire.beginTransmission(CMPS11_ADDRESS);  //starts communication with CMPS11
    Wire.write(ANGLE_8);                     //Sends the register we wish to start reading from
    Wire.endTransmission();

    // Request 5 bytes from the CMPS11
    // this will give us the 8 bit bearing,
    // both bytes of the 16 bit bearing, pitch and roll
    Wire.requestFrom(CMPS11_ADDRESS, 5);

    while (Wire.available() < 5);       // Wait for all bytes to come back

    angle8 = Wire.read();               // Read back the 5 bytes
    high_byte = Wire.read();
    low_byte = Wire.read();
    pitch = Wire.read();
    roll = Wire.read();

    // Calculate the 16 bit compass bearing from the machine
    angle16 = high_byte;                 // Calculate 16 bit angle
    angle16 <<= 8;
    angle16 += low_byte;
    raw = (angle16 / 10);

    vals += raw;
  }
  smooth = vals / cycles;

  return smooth;

}


// SET PID values based on the sample time selected by the user

void SetTunings()
{
  float SampleTimeInSec = (float(SampleTime) / 1000); //Calibrates to seconds
  Pgain = Pgain;              //No change to proportional component since it is not time dependant
  Igain = Igain * SampleTimeInSec;
  Dgain = Dgain / SampleTimeInSec;
}



//Figure out the difference between two compass bearings, including sorting out the 360 degree issue
int CompassError(int demand, int input) {
  int Merror = input - demand;
  abserror = abs(Merror);
  if (abserror > 180) {
    if (Merror < 0) {
      Merror = (360 - abserror);
    }
    else {
      Merror = -(360 - abserror);
    }
  }
  return Merror;
}









// PID subroutine
int PID(int error, unsigned long pidnow) {
  static int pidlast;
  static int lastInput;
  static int ITerm;
  static int Output;
  static int lastError;

  int timeChange = (pidnow - pidlast);
  if (timeChange >= SampleTime)   {
    /*Compute all the working error variables*/

    //Calculate Integral term, and bound it to prevent drift-off


    ITerm += float(Igain * error * Ogain);

    if (ITerm > outMax) {
      ITerm = outMax;
    }
    else if (ITerm < outMin) {
      ITerm = outMin;
    }

    //In a modification to the traditional integral term I reset it ever time the error crosses 0.  This is to prevent windup, because my output is a velocity on a fixed ram, as opposed to, say a spinning wheel.

    if ((lastError <= 0) && (error > 0)) {
      ITerm = 0;
    }
    if ((lastError >= 0) && (error < 0)) {
      ITerm = 0;
    }

    if (error == 0)  {
      ITerm = 0;
    }




    int dInput = CompassError(lastInput, filterbearing);  //For the proportional term we use - dinput error rather than +derror because it avoids the deriviative kick issue.  Note the reversal of the error calculation to take this signage into accout.  Note also there is no time component present, because this value is only worked out at regular (SampleTime) intervals


    /*Compute PID Output*/
    if (abs(error) > deadband) {   //Dont output if in deadband

      Output = (Ogain * Pgain * error + ITerm - Ogain * Dgain * dInput);
    }
    else {
      Output = 0;
    }
  /*Remember some variables for next time*/
  lastInput = filterbearing;
  lastError = error;
  pidlast = pidnow;

  return Output;
}
}




















