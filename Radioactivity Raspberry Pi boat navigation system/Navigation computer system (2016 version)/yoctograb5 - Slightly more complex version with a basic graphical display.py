#Note, this is the first version in Python to try and use the gui...
#Note also that these early versions had a bug in the GUI - I didnt realise that once a graphic line has been created it has a "Name"
#This means that it resides in the system.  In this code every time the compass updates a new line is created and the old one remains in memory.
#After ten to twenty minutes this slows the code down because it is redrawing hundreds of lines each loop.
#This has been fixed in later versions.
#The means to fix it is 
#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,sys
# add ../../Sources to the PYTHONPATH
# You will need to update this yourself to match the locations of your installed Yocto API - see YOCTO website and documentation
sys.path.append(os.path.join("..","..","Sources"))
from yocto_api import *
from yocto_tilt import *
from yocto_compass import *
from yocto_gyro import *
from yocto_accelerometer import *
import time
from Tkinter import *
import math

#Default initial magnetic declination in degrees
Mag_dec=-3

#Setup display variables
lab_text_size = 12  #Lable text size
com_text_size = 50  #Compas reading text size
Disp_bearing=0      #Initial display bearing
Bear_label_text =   "Magnetic Bearing"

Wsx=800     #window size x
Wsy=800     #window size y
Dh=550      #height of dial canvas
Ccx=Wsx/2   #Compass centre x
Ccy=250     #Compass centre y
Cd=336      #Compass diameter
Cnl=155     #Compass Needle length
Cnx=Ccx     #Initial needle end x
Cny=Ccy-Cnl #Initial needle end y


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
compass = YCompass.FindCompass(serial + ".compass")

#Setup GUI objects
CW = Tk()
CW.geometry("800x800")
CW.title('Basic Navigation')



#Setup dial frame
dialcanvas = Canvas(CW, width=Wsx, height=Dh)
dialcanvas.pack()
photo = PhotoImage(file = 'compassrose.gif')
dialcanvas.create_image(Ccx,Ccy, image=photo)
dialcanvas.create_oval(Ccx-(Cd/2),Ccy-(Cd/2),Ccx+(Cd/2),Ccy+(Cd/2), outline="red",fill="#321000", width=10)
d = [32,40,12]
dialcanvas.arrowshape = d
#Note, in later versions this buggy bit below was replaced with something like "Compassneedle=dialcanvas.create_line..."
#The "Compassneedle" object was then "Updated" each loop.  This removed the slowing down issue alluded to above.
dialcanvas.create_line(Ccx,Ccy,Cnx,Cny, fill="red", width=4, arrow="last",arrowshape=d)




#Setup text frames
mainframe = Frame(CW)
mainframe.pack()


#Setup Magnetic Bearing Label
Cbt=StringVar()
Cbt.set('')
Bear_Val=Label(dialcanvas,textvariable=Cbt,bg='#321000',fg='#000fff000',font=("Helvetica",com_text_size))
Bear_Label=Label(dialcanvas,text=Bear_label_text,bg='#321000',fg='#000fff000',font=("Helvetica",lab_text_size))
Bear_Val.place(x=340, y=200)
Bear_Label.place(x=330, y=265)




#Function used to get the compass magnetic bearing
def mag_get():
    global Disp_bearing
    Mag_bearing=round(compass.get_currentValue(),0)
    if Mag_bearing==Disp_bearing:
        changestate=0
    else:
        changestate=1
        
    Disp_bearing=Mag_bearing
    True_bearing=Mag_bearing+Mag_dec
    if Mag_bearing<100:
        if Mag_bearing<10:
            Cbt.set('00%d' % (Disp_bearing))
        if Mag_bearing>9:
            Cbt.set('0%d' % (Disp_bearing))
    else:
        Cbt.set('%d' % (Disp_bearing))
    return changestate   
   


def com_needle(Disp_bearing):
    global Cnx
    global Cny
    global Cnl
    global Ccx
    global Ccy
    global d
    dialcanvas.create_line(Ccx,Ccy,Cnx,Cny, fill="#321000", width=4, arrow="last",arrowshape=d)
    dialcanvas.update()
    radia=math.radians(Disp_bearing)
    Cnx=round(Ccx+Cnl*math.sin(radia))
    Cny=round(Ccy-Cnl*math.cos(radia))  #Note, because of the arse-wise coordinate system the Y term has to be inverted
    dialcanvas.create_line(Ccx,Ccy,Cnx,Cny, fill="red", width=4, arrow="last",arrowshape=d)
    dialcanvas.update()



#Main loop for updating GUI
while True:
    mag_change_state=mag_get()
    if mag_change_state==1:
        com_needle(Disp_bearing)

 



CW.mainloop()


