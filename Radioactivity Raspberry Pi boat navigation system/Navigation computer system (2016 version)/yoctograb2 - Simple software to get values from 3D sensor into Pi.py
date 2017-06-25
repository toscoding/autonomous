#Note, this is the first version in Python that actually works...
#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,sys
# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("/home/pi/Yocto/Sources"))
from yocto_api import *
from yocto_tilt import *
from yocto_compass import *
from yocto_gyro import *
from yocto_accelerometer import *

#Name of my Yocto3D device
yn="Y3DMK001-5558D"
target=sys.argv
errmsg=YRefParam()
if YAPI.RegisterHub("usb", errmsg)!= YAPI.SUCCESS:
    sys.exit("init error"+errmsg.value)

YAPI.RegisterHub("usb", errmsg)
anytilt = YTilt.FirstTilt()
m=anytilt.get_module()
serial=anytilt.get_module().get_serialNumber()

#Define objects needed to return values
tilt1 = YTilt.FindTilt(serial + ".tilt1")
tilt2 = YTilt.FindTilt(serial + ".tilt2")
compass = YCompass.FindCompass(serial + ".compass")
accelerometer = YAccelerometer.FindAccelerometer(serial+".accelerometer")
gyro = YGyro.FindGyro(serial + ".gyro")




count=0
print "Press ctrl-C to exit"
try:
    while True:
        if (count % 10 == 0): print "Roll   Pitch   compass acc     gyro"
        print(  "%-7.1f "%tilt1.get_currentValue() + \
               "%-7.1f "%tilt2.get_currentValue() + \
               "%-7.1f "%compass.get_currentValue() + \
               "%-7.1f "%accelerometer.get_currentValue() + \
               "%-7.1f"%gyro.get_currentValue())
        count=count+1
        YAPI.Sleep(250, errmsg)
except KeyboardInterrupt:
    pass
