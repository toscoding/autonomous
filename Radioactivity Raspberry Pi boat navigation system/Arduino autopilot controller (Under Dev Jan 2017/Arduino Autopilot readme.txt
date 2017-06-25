Note to users:
This software is very much in development.
V1.7 was the first version I took to sea.  It functioned, but the PID settings were incorrect, and experience with the interface led to a number of significant changes.

These are being incorperated in the V2.0 series of software.  Key improvements as of V2.3 are:
1: Much improved bearing averaging.  You have the option to sample around 100 values , which, if you plot them with SerialPlotter will show a significant improvement.  The number of values can be set by altering the "NumReadings" variable.
2: A "Nudge" mode.  The original overide function required buttons 1 or 2 to be held down for a "Long" period (Set at 1000ms using the "Longhold" variable).  In practice at sea this was not ideal, so I have added the "Nudge" function, which is only available when not in automatic mode.  When buttons 1 or 2 are pressed rapidly and released, the motor will move for a fixed period of time, at a fixed speed, set by altering the "NudgeTime" and "NudgeSpeed" variables.
3: P, I and D values displayed instead of Error, Current and Voltage.  At some stage I will upgrade to a scrolling display.
4: Improved floating point error measurements.
5: Mathmatical improvements to the PID routine, to ensure it correctly uses floating point values.
6. Bluetooth ajustable PID, Smoothing sample and deadband ajustment using a mobile phone app, created using MIT app inventor.  In addition you can overide the rudder, essentially using your phone as a remote control.  This is called "Autopilot_PID.aia" in this folder.  If you go on the MIT app inventor website you will find out how to install it on your Android phone.  If nothing else it looks cool.

Ultimatly I may upgrade the phone app to a full supervisor, given that the phone has GPS and can supervise a course...

If the version 2 series still dont want to play I plan to re-develop it using a slightly diffent control philosophy where discrete rudder movements are made rather than continuous.  I have nicknamed this "Nudge" control but although I have a feeling it will work it seems less refined...

