

String datestring = "Olly Epsom Apr 2017 ";
String versionstring = "Software Version 2.3";

/*
  12 April 2017
  First of the new generation software packages.
  Version 1.7 was tested at sea 09 April 2017 and the automatic mode was worse than useless.
  Version 2.1 was tested at sea 17 April 2017 with the mobile phone connectivity for gain alteration.
  Averaging system worked well but gains appeared too high even when ajusted with mobile app.
  Nudge mode proved really useful.
  Version 2.3 and ascociated mobile app have had minor error correction to allow actual lowered gains
  Includes bluetooth deadband ajustment with updated app
  Propose automatic sea state detector by altering deadband size based on the standard deviation of the averaged compass readings, but need to think about that.
  Includes ATAN2 based smoothing to deal with the "Varying around 0 degrees" aspect
  Includes time based sampling rate of 5 hz, user definable
  Slightly tidied code including beep suproutine and LCD refresh subroutines to remove the number of coded wipes.
  Code starting to get pretty messy so really needs tiding up as even I am struggling with some of it and I wrote it!

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
float pi = 3.1415;           // Pretty obvious what this is...
unsigned char high_byte, low_byte, angle8;
char pitch, roll;
unsigned int angle16;
const int headlength = 5;       //grab this number of values for smoothed bearing
int smoothedbearing;            //Sum average of a rapid grab of "Headlength" number of compass bearings
int samfreq = 5;               //Sampling frequency in Hz
int sambeat = 1000 / samfreq;  //Sampling time in miliseconds
int samtime = 2;                //Sampling time in seconds
int NumReadings = int(samfreq * samtime); //Number of readings for the continuous average

float sinreadings[50];          //Large array for holding the Sin values of the heading for smoothing using the ATAN2 method
float cosreadings[50];          //Large array for holding the Cos values of the heading for smoothing using the ATAN2 method

int filterposition = 0;         //This cycles around the array, adding each value to it
float filterbearing;            //Smoothed bearing
int coursedemand;               //Demanded course
int resumedemand;               //Stored demand, called when "Resume" is pressed
float headingerror;             //Heading error
int abserror;                   //ABS error, used for sign correction
int DeadBand = 5;               //Deadband withinwhich nothing happens - ABS(error) has to be greater than this. Measured in degrees
const int motordirection = -1;      //Change this if the motor is giving positive rather than negative feedback (If wires are connected properly this should be -1 so that the demand is the opposite direction to the error.)
const int minmotorspeed = 20;       //Do not turn motor on until a power of at least this value is demanded.
boolean dirselect = true;           //Used to set the direction when ram movement selected
int testprog = 2;                       //Inhibit motor movements in this ptorgram mode - switch to 3 to de-inhibit


// Set PID controller values

float Pgain = 0.5;            //Proportional gain for the system units of output (0-255) per degree of error
float Igain = 0;              //Integral gain for the system in units of output (0-255) per (Error in degrees * time in seconds) - Please make it an even number
float Dgain = 0;              //Differential gain for the system units of output (0-255) per (Delta Error/second) - Please make it an even number
int Ogain = 5;                //User definable gain setting which is altered by pressing button 5.  The entire P, I and D output value is multiplied by Ogain during output calculations.
int Mgain = 10;               //Maximum permitted value of Ogain
int Again = 1;                //Steps to ajust Ogain by
int tmr;                      //General purpose ticker variable
int SampleTime = 500;         //Time interval for PID in Miliseconds - The above values are then tuned
int NudgeTime = 400;          //If the ram is "Nudged", minimum time the motor is to remain on
unsigned long NudgeStart = 0; //Timer to count the nudgetime
int NudgeSpeed = 100;         //Speed of Ram for nudge mode, out of 255
int outMax = 100;             //Max integral component out of 255
int outMin = -100;            //Min integral component out of -255
int BlueCommand = 50;         //Value into which Serial commands are sent via Bluetooth if applicable
int BlueNothing = BlueCommand;//Default do-nothing for Serial link
int BlueOver = 0;             //Motor speed due to Blue Override

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
int buttonpress = 0;                  //This becomes a number from 1 to 12 if a button is pressed

int corinput = 0;                     //Triggered to -1 or +1 if button 1 or 2 pressed, and + or - tack angle if 5 or 6 pressed
const int tackangle = 100;            //Angle to tack through if buttons 5 or 6 pressed in mode
boolean manflag = false;              //Flag for manual overide is not engaged
boolean manmove = false;              //If true overpowers iSpeed to max
const int longhold = 1000;             //Duration in miliseconds needed before a button is considered held for  "Long" time


//Define flashing and warning timers
unsigned long StartTime = millis();
unsigned long CurrentTime = millis();
unsigned long ElapsedTime = CurrentTime - StartTime;
unsigned long ElapsedSample = ElapsedTime;
int flashdur = 500;                     //Flash interval
boolean alarm = false;                  //Alarm is "Off"
boolean warning = false;                //LED1 is "Off"
boolean warningrst = true;              //goes false during warning flashing phase when autopilot still active










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
  lcdrefresh(0, 0, 0, "RADIOACTIVITY");
  delay(300);
  digitalWrite(alarmpin, LOW);
  digitalWrite(LED1, LOW);
  lcdrefresh(0, 1, 0, "Autopilot control");
  delay(300);
  digitalWrite(alarmpin, HIGH);
  digitalWrite(LED1, HIGH);
  lcdrefresh(0, 2, 0, datestring);
  delay(300);
  digitalWrite(alarmpin, LOW);
  digitalWrite(LED1, LOW);
  lcdrefresh(0, 3, 0, versionstring);
  delay(2000);
  lcdrefresh(0, 0, 0, "Msg=       Program=");
  lcdrefresh(0, 1, 0, "Cts=     D Hdg=    D");
  lcdrefresh(0, 2, 0, "Mot=     % P  =     ");
  lcdrefresh(0, 3, 0, "I  =       D  =     ");

  Serial.begin(9600); // Default communication rate of the Bluetooth module

}/*--(end setup )---*/












// The loop routine runs over and over again forever.
void loop() {

  CurrentTime = millis();

  if (CurrentTime - ElapsedSample > sambeat) {

    smoothedbearing = bearinggrab(headlength);
    filterbearing = bearingaverage(smoothedbearing);
    ElapsedSample = CurrentTime;
  }

  //set default course demand if system is in mode 0
  if (prgmode == 0) {
    coursedemand = filterbearing;
    if (lastprg == 0) { //For the first time the system is turned on, the resume demand will be the course demand, otherwise it will be the last selected course
      resumedemand = coursedemand;
      lastprg = 1;    //Set the default program to 1 the first time the autohelm is started.
    }
  }


  // Calculate heading error, account for deadband, and work out motor demand, provided autopilot is active - Deceptivly simple part of the program given that this is the main function of the autohelm

  headingerror = CompassError(filterbearing, coursedemand);
  if (abs(headingerror) < DeadBand) {
    headingerror = 0;
  }

  //Program number one - rudder velocity proportional to error
  if (prgmode == 1) {
    iSpeed = PID(headingerror, CurrentTime);      //Calculate output to motor to correct heading error
  }
  else {
    iSpeed = 0;
  }



  //Programme number 2 - To be developed
  if (prgmode == 2) {


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
    // Note this could not be done with constrain in the step above, because if iSpeed was 0 it would be "Constrained" to minmotorspeed
    if (iSpeed < minmotorspeed) {
      iSpeed = 0;
    }
  }
  else {
    iSpeed = NudgeSpeed; //Default to nudge value
    if ((buttonpress == 7) || (buttonpress == 8)) {
      iSpeed = 255; //If long button press in use use full ram speed
    }
    if (BlueOver != 0) {
      iSpeed = abs(BlueOver); //If a serial command has come in, run the ram at that demanded speed
    }
  }

  powerpercent = iSpeed / 2.55;  //Percentage motor power for display, defaults to a positive value

  if (dirselect == true) {       //Inverts percentage if motor reversing
    powerpercent *= -1;
  }


  // Set motor to work
  if (prgmode != testprog) { //Only activate the motor in PWM mode if program system not in the test program mode, which is set in the paramaters at the start
    analogWrite(pinPwm, iSpeed);
    digitalWrite(pinDir, dirselect);
  }


  //Measure and calculate power demands

  voltread = analogRead(voltagepin);   // read the input pin for voltage
  curread = analogRead(currentpin);   // read the input pin for current
  voltdis = voltread * voltagecal;
  curdis = ((voltread - curread) * voltagecal) / curris;
  poweruse = voltdis * curdis;





  //Bluetooth interface command
  BlueCommand = bluescan();  //Reads a number between 0 and 255 that has been sent over the Serial link.  We assume thats bluetooth from the phone app but could be via arduino serial monitor
  if (BlueCommand != BlueNothing) {
    //Beep if Bluetooth command received, whether or not its reasonable.
    if (BlueCommand != 255) {
      beep();
    }

    if (BlueCommand == 255) {
      //No serial command received
    }
    else if (BlueCommand > 235) {
      //Do nothing at this stage but these digits are left free for future work - Up to 19 commands available
    }
    else if (BlueCommand > 215) {
      //Alter the size of the deadband
      DeadBand = (BlueCommand - 215) / 2; //Note the phone works in total deadband, the arduino in ABS deadband - i.e, a total deadband of 20 would be -10 to +10 error, which is ABS 10.
      lcdrefresh(4, 0, 7, "Dead=" + String(DeadBand));
      delay (500);

    }
    else if (BlueCommand > 189) {
      //Alter number of sample values
      NumReadings = (BlueCommand - 190) * 2;
      lcdrefresh(4, 0, 7, "Sam=" + String(NumReadings));
      delay (500);


    }
    else if (BlueCommand > 159) {
      //Alter Differential Gain and tune for the sampletime
      Dgain = ((BlueCommand - 160) / 20.0) / (float(SampleTime) / 1000);
    }
    else if (BlueCommand > 129) {
      //Alter Integral Gain and tune for the sampletime
      Igain = ((BlueCommand - 130) / 20.0) * (float(SampleTime) / 1000);
    }
    else if (BlueCommand > 99) {
      //Alter Proportional Gain
      Pgain = (BlueCommand - 100) / 20.0;
    }
    else if (BlueCommand >= 0) {
      //Serial link control of ram speed by setting up values and flags
      BlueOver = (BlueCommand - BlueNothing) * 5;
    }
  }
  else if ((manflag == true) && (BlueOver != 0)) {
    BlueOver = 0;
  }




  //User interface control

  buttonpress = buttonscan();            //This returns a number from 0 to 12 which represents the status of the buttons.  System is not capable of identifing if more than one button is pressed, it simply takes the highest one and uses that.


  //Beep if button pressed
  if ((buttonpress > 0) && (manflag == false)) {
    beep();
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

    }

    //Beep to indicate program selections
    for (tmr = 0; tmr < (prgmode + 1); tmr ++) {
      delay(100);
      beep();
    }

    delay(1000);
  }






  //Handle manual overide - Quite complicated hence the code - If in mode 0 buttons 1 and 2 "Nudge" the ram directly for a short period - Mode added after experience at sea.
  //If in any mode and buttons 7 and 8 are pressed, they move the ram directly until the buttons are released.  If in mode >0 autopilot disengage but can be resumed by pressing button 5
  //If in mode >0 buttons 1 and 2 alter the CTS



  // Handle correction of course
  if ((buttonpress == 1) || (buttonpress == 7) || (BlueOver > 0)) {
    corinput = -1 * motordirection;
    dirselect = false;
    dismsg = 4;

  }


  if ((buttonpress == 2)  || (buttonpress == 8) || (BlueOver < 0)) {
    corinput = 1 * motordirection;
    dirselect = true;
    dismsg = 5;

  }


  // Set manual movement flags if called for
  if ((buttonpress == 1)  || (buttonpress == 2) || (buttonpress == 7) || (buttonpress == 8) || (BlueOver != 0)) {
    if ((prgmode == 0) || (buttonpress == 7) || (buttonpress == 8) || (BlueOver > 0)) { //This statement prevents the system dropping out of automatic mode if buttons 1 or 2 are pressed in automatic mode, since in that case they have a different function
      NudgeStart = CurrentTime;
      manflag = true;
      manmove = true;
      prgmode = 0;
      digitalWrite(LED1, LOW); //Turn off program selection LED
    }

  }

  // Reset manual movement flags if called for
  if ((manflag == true) && (buttonpress == 0) && (CurrentTime - NudgeStart > NudgeTime) && (BlueOver == 0)) {
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


  //Display infomation on LCD display - Significant improvement in code efficency as I have a routine which wipes and prints

  lcdrefresh(4, 0, 7, usrmsg[dismsg]);
  lcdrefresh(19, 0, 1, String(prgmode));
  lcdrefresh(4, 1, 3, String(coursedemand));
  lcdrefresh(15, 1, 3, String(int(filterbearing)));
  lcdrefresh(4, 2, 4, String(powerpercent));
  lcdrefresh(15, 2, 4, String(Pgain));
  lcdrefresh(4, 3, 4, String(Igain));
  lcdrefresh(15, 3, 4, String(Dgain));

  // *******End of main loop *******
}
























// **** important subroutines start here ***


//beep routine
int beep() {
  digitalWrite(alarmpin, HIGH);
  delay(100);
  digitalWrite(alarmpin, LOW);
}


//Function prints a set of spaces at a given location of the LCD screen, followed by the text value called
void lcdrefresh(int x, int y, int l, String t) {

  lcd.setCursor(x, y);
  for  (int i = 0; i < l; i++) {
    lcd.print(" ");
  }

  lcd.setCursor(x, y);
  lcd.print(t);

}






//Check and return button status
int buttonscan() {
  int pressed = 0;
  static boolean buttonarray[3][6] = {{false, false, false, false, false, false}, {false, false, false, false, false, false}}; //Array for handing button controls
  static unsigned long buttontime[6];

  // Return from this function is a number from 0 to 12.  0 is no button pressed.  1-6 is the buttons pressed in instantaneous mode.  7-12 is the buttons pressed in "Long" mode.
  // Clever thing about this is that it runs whilst the rest of the program is running, by storing the button status as "Flags".
  // It does not return a value greater than zero until a button has been pressed AND released, at which point the value will be 1-6 if its been pressed and released quickly, or 7-12 if its been latched.

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






















// Grab heading out of compass and give it an inital smooth - Does not use ATAN2 method as it happens so fast that in practice I have never had an issue
int bearinggrab(int cycles) {
  float smooth = 0;
  float raw = 0;
  float vals = 0;

  //I think this section is the only non-Olly Epsom written code
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
    raw = (angle16 / 10.0);

    vals += raw;
  }
  smooth = (vals / cycles);
  return smooth;

}

//Add values to the array and filter them - Uses the Atan2 method in order to prevent skipping when the incomming values are in the 355-005 degree range - otherwise averages might be 180!
float bearingaverage (float hdgvalue)   {
  float radianhdg = hdgvalue / (360 / (2 * pi));
  float sumvalues = 0;
  float raw = 0;
  float sumsin = 0;
  float sumcos = 0;
  float rawresult = 0;
  float filteredresult = 0;
  float StdDevHdg = 0;

  //Load value into scrolling array
  sinreadings[filterposition] = sin(radianhdg);
  cosreadings[filterposition] = cos(radianhdg);
  filterposition += 1;
  if (filterposition == NumReadings) {
    filterposition = 0;
  }

  //Add up all the values and average them
  for (int i = 0; i < NumReadings; i++) {
    raw = sinreadings[i];
    sumsin += raw;
    raw = cosreadings[i];
    sumcos += raw;

  }

  //Calculate Standard Deviations of sins and cos and angle resulting.
  StdDevHdg = (atan2(stddev(cosreadings, (sumcos / NumReadings), NumReadings), stddev(sinreadings, (sumsin / NumReadings), NumReadings)) * (360 / (2 * pi)));
  //StdDevHdg = stddev(sinreadings, (sumsin / NumReadings),NumReadings);

  //Recalculate angle based on average sin and cos readings.
  //There is some faffing here because arduino converts to +- pi radians starting from the X axis which is 90 degrees opposed to our Y axis base.
  rawresult = float(atan2((sumcos / NumReadings), (sumsin / NumReadings)) * (360 / (2 * pi)));

  if ((rawresult > -180) && (rawresult < 90)) {
    filteredresult = 90 - rawresult;
  }
  else {
    filteredresult = 450 - rawresult;
  }


  Serial.print (hdgvalue);
  Serial.print (",");
  Serial.print(filteredresult);
  Serial.print (",");
  Serial.print (coursedemand);
  Serial.print (",");
  Serial.println (iSpeed);

  return filteredresult;

}


//Routine for finding the standard deviation of a sample
float stddev(float(SamArray[]), float(SamMean), int NumVals) {
  float raw;
  float stddevr = 0;

  for (int i = 0; i < NumVals; i++) {
    raw = (SamArray[i] - SamMean);
    stddevr += raw * raw;
  }
  stddevr = sqrt(stddevr);
  return stddevr;

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
float CompassError(float input, float demand) {
  float Merror = demand - input;
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




//Read Bluetooth or other serial Check and return button status
int bluescan() {
  unsigned long received = 255;

  if (Serial.available() > 0) { // Checks whether data is comming from the serial port
    received = Serial.read(); // Reads the data from the serial port
  }

  return received;
}







// PID subroutine
int PID(float error, unsigned long pidnow) {
  static int pidlast;
  static float lastInput;
  static float ITerm;
  float OutputF;
  static int Output;
  static float lastError;

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




    float dInput = CompassError(lastInput, filterbearing); //For the proportional term we use - dinput error rather than +derror because it avoids the deriviative kick issue.  Note the reversal of the error calculation to take this signage into accout.  Note also there is no time component present, because this value is only worked out at regular (SampleTime) intervals


    /*Compute PID Output*/
    OutputF =  (Ogain * Pgain * error + ITerm - Ogain * Dgain * dInput);
    Output = OutputF; //Integerise OutputF

    /*Remember some variables for next time*/
    lastInput = filterbearing;
    lastError = error;
    pidlast = pidnow;

    return Output;
  }
  //Else do nothing because the sampletime hasnt elapsed yet
}





















