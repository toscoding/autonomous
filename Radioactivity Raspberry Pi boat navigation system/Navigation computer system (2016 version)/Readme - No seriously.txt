Olly Epsom [Drawingboard82], Bishopbriggs, Glasgow, 02 January 2017

Welcome to hours of fun!

To run these programes you must install the relevant APIs from the sensors that you are using.

You will also need to find the unique names of your sensors as seen by the USB.

Lots of help online on how to do this.

These programes run in the root mode and for some reason only work in a path like this:

/root/Yoctopython/Examples/Doc-GettingStarted-Yocto-3D

I have been meening to fix that and havent got around to it.

To get started:

Yoctograb 2 is a simple program to get the infomation from the 3D sensor.
GPSgrab does a similar thing for the GPS sensor.

Once you have those two sensors working you are basicly home and dry - The rest is 
user interface which you can customise to your hearts content.

NavAttack3 is the 2016 spec all singing all dancing nav system described in my Youtube videos
It requires DMSmodule which is a series of long-winded mathmatical formula
Mainly to do with calculating range and bearings, formating the incomming data and so on.
In additon there are textfiles "Coastlats", "Coastlongs" and "Waypoints"
These would need to be customised to your own area.
(I created them with a utility program which allowed me to click over a snapshot from google)

Hopefully much of this can be extracted by you for use in your own projects.

Over the winter of 2016-2017 I am planning on over-haul and minor re-write
For example, the Vario Meter still doenst work paticuarly well and I plan to remove it.
Other plans:
Re-format graphics to take into account how I use it.  Possibly page based
Somehow link to NMEA instruments to get a true-wind display.
Link an ADC into the pi to measure voltage and current
Remove the soft MOB function since the hard-wired one is way more practical.
Make a "MOB reset" function - currently once its pressed the MOB marker remains there forever, or until its pressed again.
Incorperate bluetooth to talk to the Arduino autopilot I am also building
Display data sent by the arduino autopilot and transmit instructions to it.

Any (Sensible!) questions please give me a bell

Happy programming.

Olly