versiontext='Navigation and Attatck System 5.0 Amal Attaturk'


#NavAttack system 5.0 June 2017
#This is a major rewrite which has been constructed
#to include wind speed and direction data from the metmast unit.
#It recycles most of the code from version 4.0
#Vario has been removed as never really worked
#Layout now a tabbed interface.
#Various improvements to make the programme run faster
#NaN errors removed and subsequently updated on Version 4
#Integration with MetMast included




print ('importing data')

import os,sys
# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("/home/pi/Yocto/Sources"))
from yocto_api import *
from yocto_tilt import *
from yocto_compass import *
from yocto_gyro import *
from yocto_accelerometer import *
import time
from Tkinter import *
import math
import os
from gps import *
import threading
import ttk
import csv
import numpy
import dmsmodule
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO
import bluetooth

#We are using GPIO 4 as the input for the hard wired MOB button.
#I have always thought GPIO 4 is the lucky pin!

GPIO.setmode(GPIO.BCM)
GPIO.setup(4,GPIO.IN)


print (versiontext)
print('data imported')


#Simulation or real mode settings
#simmode is a vector. 0=normal, 1 = simulation
#First figure = Simulate GPS course
#Second figure = Simulate GPS speed
#Third figure = Simulate Magnetic course
#Forth figure = Simulate a moving GPS course

simmode=[0,0,0,0] #For use in simulation mode.  
simcount=1

#Data for simulating a course
#Lat, Long, Course, Speed, Starting time
sim_course_data=[55.772733,-4.861865,220,5,time.time()]



#Function for checking which aspects of the program are in simulation mode
def simcheck(simmode):
    if simmode[0]==1:
        print "WARNING! ***GPS course in simulation mode***"

    if simmode[1]==1:
        print "WARNING ***GPS speed in simulation mode***"

    if simmode[2]==1:
        print "WARNING ***Magnetic bearing in simulation mode***"


#For-loop function, very useful
def sequencing(start, stop, step=1):
    n = int(round((stop - start)/float(step)))
    if n > 1:
        return([start + step*i for i in range(n+1)])
    else:
        return([])

simcheck(simmode)
newtable=sequencing(0,3.1415*2,0.1)
simtable = [math.cos(i) for i in newtable]





#Default initial magnetic declination in degrees
Mag_dec=-3


#Setup display variables
lab_text_size = 12
com_text_size = 40
s_text_size = 40
back_ground_colour="#421000"
dial_colour="red"
needle_colour="red"
tracking_colour="#999fff222"
upwind_colour="yellow"
apparent_wind_colour="blue"
true_wind_colour = "green"
text_colour="#000fff000"
text_font="Ariel"
horizon_colour='#000000333'
horizon_fill="gray50"
my_dpi=80 #DPI of display, used by charts
boat_colour='m'
Disp_bearing=0
Wsx=1000    #window size x
Wsy=800     #window size y
Tabx=800    #Notebook page sizes
Taby=730    #Notebook page sizes
Dh=720      #height of dial canvas
arrowhead = [32,40,12] #Proportions of arrow size
Ccx=Tabx/2  #Compass centre x
Ccy=Dh/2    #Compass centre y
Cd=550      #Compass diameter
Cnl=350     #Compass Needle length
Tnl=330     #Tracking needle length
Cnx=Ccx     #Initial needle end x
Cny=Ccy-Cnl #Initial needle end y
Nx=6.5      #Width of nav chart in inches (!!)
Ny=5.5      #Height of Nav chart in inches  
Spx=396     #Speed dial x
Spy=107     #Speed dial y
Spd=200     #Speed dial diameter
Spl=100     #Speed dial length
Snx=Spx     #Initial speed dial x
Sny=Spy+Spl #Initial speed dial y
Unx=Spx     #Upwind needle initial position
Uny=Sny     #Upwind needle initial position
Perx=396    #Performance dial centre X
Pery=365    #Performance dial centre Y
Wrx=396     #Performance relative wind x
Wry=200     #Performance relative wind y
Wtx=396     #Performance true wind x
Wty=200     #Performance true wind y
Pwol=380    #Outer radius of performance needles
Pwil=150    #Inner radius of performance needles


MOB_reset=0 #Man Overboard button not pressed

#Perihpheral artifical horizon coordinates
pahr=800
pahx1=Ccx-pahr
pahx2=Ccx+pahr
pahy1=Ccy
pahy2=Ccy

#Setuo navigational variables
yn="Y3DMK001-5558D"             #Name of my Yocto3D device - You will need to edit for your device
bl=['','']                      #Blank data to be loaded into arrays
basic_nav_data=[bl]*20          #Blank navigation data list
process_nav_data=basic_nav_data #Processed navigation data list
O_p_n_d=[0]*20                  #Used for anti flicker
soft_correct=8                  #Soft correction for compass - i.e, its been installed on the wonk
time_data=range(100,-1,-1)      #Array of last 100 seconds
keitems=100                     #Number of items in KE arrays
roll_data=[0]*keitems           #Array of historical roll data
pitch_data=[0]*keitems          #Array of historical pitch data
speed_data=[0]*keitems          #Array of historical speed data
ke_data=[0]*keitems             #Array of historical Kinetic Energy data
atmitems=100                    #Number of items in Atmospheric arrays
true_wnd_spd_data=[0]*atmitems  #Array of historical True Wind speed data
true_wnd_dir_data=[0]*atmitems  #Array of historical True Wind Direction data (Absolute)
temp_deg_data=[0]*atmitems      #Array of historical temperature data
press_mbar_data=[0]*atmitems    #Array of historical atmpspheric pressure data
pr=0                            #Nominal recording precision - 0 is every second
lo_cation_axis=[-5.556118,-4.225344959,55.577373,56.091903]      #Default axis for location chart (Will be updated)
his_long=[-4.857788]            #Default long (Largs Marina)
his_lat=[55.773427]             #Default lat (Largs Marina)
max_storage=500                 #Max points to store in history array
mob_lat=[0]                     #Default location of man overboard
mob_long=[0]                    #Default location of man overboard
my_long=[0]                     #Default current position for plotting
my_lat=[0]                      #Default current position for plotting
tripometer=0                    #Default value of tripometer
scale_pos=5                     #Default position in scale 
scale_choice=[0.3,0.6,0.9,1.8,3.0,6.0,9.0,12.0,15.0,18.0,27.0,30.0,45.0,60.0,90.0,180.0,270.0,360.0,450.0]
lo_cation_scale=scale_choice[scale_pos]              #Default scale for location chart in NM
boat_mass=2800                   #Mass of boat in kg

#Setup MetMast details
processed_met_data=['',1]*12     #Blank array for met data
dir_correct=0                    #Soft-correct for the wind bearing in degrees
spd_correct=1                    #Soft -correct for the wind speed in factors
tosend='8'                       #Bluetooth request number for metmast
bd_addr = '98:D3:36:00:BD:3B'    #My MetMast adress - you will have to change this for yours
port = 1                         #Port for Bluetooth
MetFitted=True                   #Turn to "False" if MetMast is not available
MetMast=None                     #Bluetooth object for MetMast comms





#Setup update periods
navchartupdate=10               #How often the navigation chart is updated in seconds
physicsupdate=6                 #How often the physics chart is updated
windupdate=1                    #How often the performance graphics are updated
atmupdate=10                    #How often the atmospheric data graphs are updated
ADCupdate=30                    #How often the ADC chart is updated

#Setup chart x value arrays
kexv=sequencing(0,99*physicsupdate,physicsupdate)        #Array of x values for KE charts
atmxv=sequencing(0,99*physicsupdate,physicsupdate)        #Array of x values for KE charts


#Setup timers for update periods
navtmr=0
phytmr=0
windtmr=0
adctmr=0
atmtmr=0




#Setup graphing variables
pane1='Atmospherics'
pane2='Physics'
pane3='Electronics'

#pane 1, chart 1, title, slope, offest and data array
p11t='Wind speed knots'
p11s=1
p11o=0
p11d=[0]*100

#pane 1, chart 2, title, slope, offest and data array
p12t='Wind direction true, degrees'
p12s=1
p12o=0
p12d=[0]*100

#pane 1, chart 3, title, slope, offest and data array
p13t='barometric pressure Mbar'
p13s=1
p13o=0
p13d=[0]*100

#pane 1, chart 4, title, slope, offest and data array
p14t='Temperature degrees'
p14s=1
p14o=0
p14d=[0]*100

#pane 3, chart 1, title, slope, offest and data array
p31t='ADC channel 1'
p31s=1
p31o=0
p31d=[0]*100

#pane 3, chart 2, title, slope, offest and data array
p32t='ADC channel 2'
p32s=1
p32o=0
p32d=[0]*100

#pane 3, chart 3, title, slope, offest and data array
p33t='ADC channel 3'
p33s=1
p33o=0
p33d=[0]*100

#pane 3, chart 4, title, slope, offest and data array
p34t='ADC channel 4'
p34s=1
p34o=0
p34d=[0]*100



# ***Setup GPS***

gpsd = None #seting the global GPS variable
 
os.system('clear') #clear the terminal screen

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer


gpsp = GpsPoller() # create the GPS thread
gpsp.start() # start it up


##Start up MetMast comms if not inhibited
print "Searching for MetMast"

class MetThread (threading.Thread):
   def __init__(self):
      threading.Thread.__init__(self)
      global MetMast
      global MetFitted
      if MetFitted==True:
          print 'Connecting to Metmast via Bluetooth'
          MetMast = bluetooth.BluetoothSocket (bluetooth.RFCOMM)
          MetMast.connect((bd_addr,port))
          print 'Got this far, press Ctrl-C to quit'
      else:
          print 'Met Mast inhibited in Software'
      self.current_value = None
      self.running = True
      
   def run(self):
      global processed_met_data
      global tosend
      global MetMast
      global dir_correct
      global spd_correct
      global MetFitted
      while MetFitted==True:
          MetMast.send(tosend)
          time.sleep(.1)
          buffer = MetMast.recv(4096)
          inbounddata=buffer
          raw_met_data=inbounddata.split("\t")
          
          if len(raw_met_data)>9:
              processed_met_data=dmsmodule.met_mast_correct(raw_met_data,dir_correct,spd_correct,process_nav_data[3][1],process_nav_data[4][1])
          time.sleep(1)

MetGrab = MetThread()   #Create MetMast thread
MetGrab.start()         #Start it up
print processed_met_data


##Load text file of waypoints
print 'Loading waypoints from text file'
with open('Waypoints.csv', 'rb') as csvfile:
    waypoints_obj = csv.reader(csvfile)
    waypoints_list=list(waypoints_obj)

#Future proof against origin
waypoints_list[0][2]=0
waypoints_list[0][3]=0

waypoints_names=["0 Origin"]*len(waypoints_list)
waypoints_lats=[0]*len(waypoints_list)
waypoints_longs=[0.0]*len(waypoints_list)
waypoints_lables=[0.0]*len(waypoints_list)


#Calibrate waypoints array
for c in range (1, len(waypoints_list)):
    waypoints_names[c]=waypoints_list[c][0]+' ' + waypoints_list[c][1]
    waypoints_lables[c]=waypoints_list[c][1]
    waypoints_lats[c]=float(waypoints_list[c][2])
    waypoints_longs[c]=float(waypoints_list[c][3])    
print 'waypoints loaded'


#Import coaslines
print 'Loading coastline infomation from files'
lats_and_longs=dmsmodule.import_coastlines('coastlats.txt','coastlongs.txt')
coast_lats=lats_and_longs[0]
coast_longs=lats_and_longs[1]
print 'Coaslines imported'


#Start up log file
print 'Setting up electronic log'
log_name='/home/pi/Navigation system software/Navigation Log files/'+str(time.ctime())+'.csv'
Nav_log_object=open(log_name, "a")
Nav_log_object.write(versiontext+'\n')
Nav_log_object.write(str(time.ctime())+'\n')
Nav_log_object.write("Time,Lat,Long,Magnetic,GPS course,speed,pitch,roll,trip\n")
Nav_log_object.close()
print 'Electronic log started. File name is:',log_name



# Setup Yocto device handling and objects
target=sys.argv
errmsg=YRefParam()
if YAPI.RegisterHub("usb", errmsg)!= YAPI.SUCCESS:
    sys.exit("init error"+errmsg.value)

YAPI.RegisterHub("usb", errmsg)
anytilt = YTilt.FirstTilt()
m=anytilt.get_module()
serial=anytilt.get_module().get_serialNumber()
accelerometer = YAccelerometer.FindAccelerometer(serial+".accelerometer")
gyro = YGyro.FindGyro(serial + ".gyro")

#Define objects needed to return values
compass = YCompass.FindCompass(serial + ".compass")
roll = YTilt.FindTilt(serial + ".tilt1")
pitch = YTilt.FindTilt(serial + ".tilt2")




#Setup GUI objects
CW = Tk()
CW.geometry("1000x800")
CW.title(versiontext)

#Setup tabbed interface
tabbedinter=ttk.Notebook(CW)
tabbedinter.place(x=0,y=0)
page1=ttk.Frame(tabbedinter,width=Tabx,height=Taby,)
page2=ttk.Frame(tabbedinter,width=Tabx,height=Taby)
page3=ttk.Frame(tabbedinter,width=Tabx,height=Taby)
tabbedinter.add(page1, text="Navigation")
tabbedinter.add(page2, text="Performance")
tabbedinter.add(page3, text="Data")

#Setup lable frames on "data" tab
datapane1=LabelFrame(page3, text=pane1,width=Tabx/3, height=Taby)
datapane2=LabelFrame(page3, text=pane2,width=Tabx/3, height=Taby)
datapane3=LabelFrame(page3, text=pane3,width=Tabx/3, height=Taby)
datapane1.place(x=0,y=0)
datapane2.place(x=Tabx*.333,y=0)
datapane3.place(x=Tabx*.666,y=0)


#Setup graphical objects on "Navigation" tab
dialcanvas = Canvas(page1, width=Tabx, height=Dh)
dialcanvas.pack()
background_box=dialcanvas.create_rectangle(0, 0, Tabx, Dh, fill=back_ground_colour)
dashboard_image_day  = PhotoImage(file = 'Squarecompassday.gif')
dashboard_image_night = PhotoImage(file = 'Squarecompassnight.gif')
dashboard_background=dialcanvas.create_image(Ccx,Ccy, image=dashboard_image_day)
peripheral_artificial_horizon=dialcanvas.create_polygon(0,Dh,pahx1,pahy1,pahx2,pahy2,pahx2,Dh,fill=horizon_colour, stipple=horizon_fill,width=4)


Compass_rose=dialcanvas.create_rectangle(Ccx-(Cd/2),Ccy-(Cd/2),Ccx+(Cd/2),Ccy+(Cd/2), outline=dial_colour,fill=back_ground_colour, width=10)
dialcanvas.arrowshape = arrowhead

#Create needle objects
compass_needle=dialcanvas.create_line(Ccx,Ccy,Cnx,Cny, fill=needle_colour, width=4, arrow="last",arrowshape=arrowhead)
tracking_needle=dialcanvas.create_line(Ccx,Ccy,Cnx,Cny, fill=tracking_colour, width=3, arrow="last",arrowshape=arrowhead)



#Setup Magnetic Bearing Label
Cbt=StringVar()
Cbt.set('')
Bear_label_text = StringVar()
Bear_label_text.set('-Magnetic Bearing-')      
Bear_Val=Label(dialcanvas,textvariable=Cbt,bg=back_ground_colour,fg=text_colour,font=(text_font,com_text_size))
Bear_Label=Label(dialcanvas,textvariable=Bear_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Bear_Val.place(x=Ccx-270,y=545)
Bear_Label.place(x=Ccx-270, y=605)

#Setup Speed lable
Spd=StringVar()
Spd.set('')
Uws=StringVar()
Uws.set('')
Spd_label_text = StringVar()
Spd_label_text.set('Speed - Knots')
Spd_Val=Label(dialcanvas,textvariable=Spd,bg=back_ground_colour,fg=text_colour,font=(text_font,s_text_size))
Spd_Label=Label(dialcanvas,textvariable=Spd_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Spd_Val.place(x=Ccx+150,y=545)
Spd_Label.place(x=Ccx+150, y=605)

#Setup vario - Not used but DMS module needs it
Vad=StringVar()
Vad.set('')

#Setup performance frame graphics
performance_canvas=Canvas(page2,width=Tabx, height=Taby)
performance_canvas.pack()
performance_canvas.arrowshape=arrowhead
performance_background = PhotoImage(file = 'Polar plot blank.gif')
dashboard_background=performance_canvas.create_image(Ccx,Ccy, image=performance_background)

#Setup needle objects
sppeed_needle=performance_canvas.create_line(Spx,Spy,Snx,Sny, fill=needle_colour, width=4, arrow="last",arrowshape=arrowhead)
uppwind_needle=performance_canvas.create_line(Spx,Spy,Unx,Uny, fill=upwind_colour, width=4, arrow="last",arrowshape=arrowhead)
per_app_needle=performance_canvas.create_line(Perx,Pery,Wrx,Wry, fill=apparent_wind_colour, width=6, arrow="first",arrowshape=arrowhead)
per_true_needle=performance_canvas.create_line(Perx,Pery,Wtx,Wty, fill=true_wind_colour, width=6, arrow="first",arrowshape=arrowhead)

#Setup wind speed lables
App_Spd=StringVar()
App_Spd.set('')
True_Spd=StringVar()
True_Spd.set('')
App_Spd_label_text = StringVar()
App_Spd_label_text.set('Apparent Wind - Knots')
App_Spd_Val=Label(performance_canvas,textvariable=App_Spd,bg=back_ground_colour,fg=text_colour,font=(text_font,s_text_size))
App_Spd_Label=Label(performance_canvas,textvariable=App_Spd_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
App_Spd_Label.place(x=Perx-350, y=10)
App_Spd_Val.place(x=Perx-350,y=35)

True_Spd_label_text = StringVar()
True_Spd_label_text.set('True Wind - Knots')
True_Spd_Val=Label(performance_canvas,textvariable=True_Spd,bg=back_ground_colour,fg=text_colour,font=(text_font,s_text_size))
True_Spd_Label=Label(performance_canvas,textvariable=True_Spd_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
True_Spd_Label.place(x=Perx+210, y=10)
True_Spd_Val.place(x=Perx+250,y=35)

#Setup atmospheric data lables
Temp_deg=StringVar()
Temp_deg.set('')
Press_mbar=StringVar()
Press_mbar.set('')
Temp_deg_label_text = StringVar()
Temp_deg_label_text.set('Air temp - Degrees')
Temp_deg_Val=Label(performance_canvas,textvariable=Temp_deg,bg=back_ground_colour,fg=text_colour,font=(text_font,s_text_size))
Temp_deg_Label=Label(performance_canvas,textvariable=Temp_deg_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Temp_deg_Label.place(x=Perx-350, y=692)
Temp_deg_Val.place(x=Perx-350,y=630)

Press_mbar_label_text = StringVar()
Press_mbar_label_text.set('Atm Pressure Mbar')
Press_mbar_Val=Label(performance_canvas,textvariable=Press_mbar,bg=back_ground_colour,fg=text_colour,font=(text_font,s_text_size))
Press_mbar_Label=Label(performance_canvas,textvariable=Press_mbar_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Press_mbar_Label.place(x=Perx+210, y=692)
Press_mbar_Val.place(x=Perx+250,y=630)




#Setup text frames which are outside of tabbed interface

modeframe = Canvas(CW,width=Wsx-Tabx, height=300)
modeframe.place(x=Tabx+10, y=20)

dataframe=Canvas(CW,width=Wsx-Tabx, height=350)
dataframe.place(x=Tabx+10, y=270)

keyframe=Canvas(CW,width=Wsx-Tabx,height=220)
key_image  = PhotoImage(file = 'Nav system key.gif')
key_show=keyframe.create_image(90,110, image=key_image)
keyframe.place(x=Tabx+10, y=600)

visualframe=Canvas(performance_canvas, width=Wsx-400, height=Wsy-Dh)
visualframe.place(x=Tabx, y=85)


#Compass mode selection Radio buttons
MTC = IntVar()         #Magnetic/True/GPS CMG variable
MTC.set(1)             #Default is Magnetic

def Mag_True_CMG():
    global Bear_label_text
    global MTC
    #Magnetic-True-CMG selection function
    if MTC.get() ==1:
        Bear_label_text.set('-Magnetic Bearing-')
    if MTC.get() ==2:
        Bear_label_text.set('-  True Bearing  -')
    if MTC.get()==3:
        Bear_label_text.set('-Course Made Good-')
    Bear_Label.update()




Label(modeframe,text = "Compass Mode",font=(text_font,lab_text_size)).place(x=10,y=0)
Radiobutton(modeframe, text="Magnetic", variable=MTC, value=1, command = Mag_True_CMG).place(x=10,y=30)
Radiobutton(modeframe, text="True", variable=MTC, value=2, command = Mag_True_CMG).place(x=10,y=50)
Radiobutton(modeframe, text="GPS CMG", variable=MTC, value=3, command = Mag_True_CMG).place(x=10,y=70)



#Magnetic Declination add
def Mag_dec_add():
   global Mag_dec
   global MDT
   Mag_dec=Mag_dec+1
   MDT.set('%d' %(Mag_dec))
   Mag_dec_label.update()


#Magnetic Declination subtract
def Mag_dec_sub():
    global Mag_dec
    global MDT
    Mag_dec=Mag_dec-1
    MDT.set('%d' %(Mag_dec))
    Mag_dec_label.update()   

#Magnetic Declination selection buttons
MDT=StringVar()
MDT.set('%d' %(Mag_dec))

Label(modeframe,text = "Magnetic Declination",font=(text_font,lab_text_size)).place(x=10,y=90)
Mag_dec_label=Label(modeframe,textvariable=MDT,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Mag_dec_label.place(x=55,y=120)
Mag_dec_minus=Button(modeframe,text="-", command = Mag_dec_sub)
Mag_dec_plus=Button(modeframe,text="+", command = Mag_dec_add)
Mag_dec_minus.place(x=20, y=120)
Mag_dec_plus.place(x=85,y=120)


#Function for setting values of day/night mode
def Day_night_mode():
    global dialcanvas
    global dashboard_image_day
    global dashboard_image_night
    
    #Magnetic-True-CMG selection function
    if DNM.get() ==1:
        ldnm=1
    if DNM.get() ==2:
        ldnm=2    
    if DNM.get() ==3:
        ldnm=1


    if ldnm ==1:
        #Daytime settings
        back_ground_colour="#321000"
        dial_colour="red"
        needle_colour="red"
        text_colour="#000fff000"
        horizon_colour="magenta"
        dashboard_file=dashboard_image_day
        
    if ldnm ==2:
        #Nightime settings
        back_ground_colour="#321000"
        dial_colour="green"
        needle_colour="blue"
        text_colour="blue"
        horizon_colour="blue"
        dashboard_file=dashboard_image_night

    #Update dial canvas objects

    dialcanvas.itemconfig(Compass_rose, outline=dial_colour,fill=back_ground_colour)
    dialcanvas.itemconfig(compass_needle, fill=needle_colour)
    dialcanvas.itemconfig(sppeed_needle, fill=needle_colour)
    dialcanvas.itemconfig(peripheral_artificial_horizon,fill=horizon_colour)

    dashboard_image  = dashboard_file   
    dialcanvas.itemconfig(dashboard_background, image=dashboard_image)
    dialcanvas.itemconfig(background_box, fill=back_ground_colour)
    dashboard_image  = PhotoImage(file = dashboard_file)
    dialcanvas.itemconfig(dashboard_background, image=dashboard_image)
    


#Day/Night mode Radio buttons
DNM = IntVar()         #Day/Night mode
DNM.set(1)             #Default mode is Day
Label(modeframe,text = "Graphics Mode",font=(text_font,lab_text_size)).place(x=10,y=150)
Radiobutton(modeframe, text="Day", variable=DNM, value=1, command = Day_night_mode).place(x=10,y=180)
Radiobutton(modeframe, text="Night", variable=DNM, value=2, command = Day_night_mode).place(x=10,y=200)
Radiobutton(modeframe, text="Auto", variable=DNM, value=3, command = Day_night_mode).place(x=10,y=220)







#Setup GPS data graphics    
Label(dataframe,text = "Select Waypoint",font=(text_font,lab_text_size)).place(x=10,y=0)
next_waypoint_name=StringVar()
next_waypoint_name.set(waypoints_names[2])

next_waypoint_range=StringVar()
next_waypoint_range.set(waypoints_names[1])

next_waypoint_bearing=StringVar()
next_waypoint_bearing.set(waypoints_names[1])

waypoint_list=ttk.Combobox(dataframe,values=waypoints_names,textvariable=next_waypoint_name,width=16)
waypoint_list.place(x=10,y=30)

Label(dataframe,text = "Next Waypoint",font=(text_font,lab_text_size)).place(x=10,y=50)

Next_waypoint_label=Label(dataframe,textvariable=next_waypoint_name,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Next_waypoint_label.place(x=10,y=75)

Next_waypoint_range=Label(dataframe,textvariable=next_waypoint_range,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Next_waypoint_range.place(x=10,y=100)

Next_waypoint_bearing=Label(dataframe,textvariable=next_waypoint_bearing,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Next_waypoint_bearing.place(x=10,y=125)

Label(dataframe,text = "Current position",font=(text_font,lab_text_size)).place(x=10,y=150)

disp_lat=StringVar()
disp_lat.set('lat ' +process_nav_data[5][1])

disp_long=StringVar()
disp_long.set('long ' +process_nav_data[6][1])

disp_course=StringVar()
disp_course.set('CMG ' +process_nav_data[3][1])

disp_time=StringVar()
disp_time.set(process_nav_data[7][1])

disp_SPD=Spd
disp_UWS=Uws


GPS_lat_label=Label(dataframe,textvariable=disp_lat,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
GPS_lat_label.place(x=10,y=175)

GPS_long_label=Label(dataframe,textvariable=disp_long,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
GPS_long_label.place(x=10,y=200)

GPS_CMG_label=Label(dataframe,textvariable=disp_course,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
GPS_CMG_label.place(x=10,y=225)

GPS_SPD_label=Label(dataframe,textvariable=disp_SPD,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
GPS_SPD_label.place(x=10,y=250)

GPS_time_label=Label(dataframe,textvariable=disp_time,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
GPS_time_label.place(x=10,y=300)

GND_SPD_label=Label(performance_canvas,textvariable=disp_SPD,bg=back_ground_colour,fg="red",font=(text_font,lab_text_size+2))
GND_SPD_label.place(x=Spx+10,y=Spy+18)

UPW_SPD_label=Label(performance_canvas,textvariable=disp_UWS,bg=back_ground_colour,fg="yellow",font=(text_font,lab_text_size+2))
UPW_SPD_label.place(x=Spx-10,y=Spy+60)

#Setup Target Bearing Label
Track_label_text = StringVar()
Track_label_text.set('Next Waypoint Bears')      
Track_Val=Label(dialcanvas,textvariable=next_waypoint_bearing,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size+6))
Track_Label=Label(dialcanvas,textvariable=Track_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Track_Val.place(x=Ccx-120,y=560)
Track_Label.place(x=Ccx-70, y=605)


#Setup charts - Long winded since there are very many charts!

#Main GPS chart on the "Navigation tab"
fig1 = Figure(figsize=(Nx,Ny),dpi=my_dpi,facecolor=back_ground_colour)
lo_cation = fig1.add_subplot(111,axisbg=back_ground_colour)
lo_cation.axis(lo_cation_axis)

waypoint_plot = lo_cation.scatter(waypoints_longs,waypoints_lats, marker='o',color='c')
curr_position,=lo_cation.plot(his_long,his_lat, 'r',linewidth=3.0)
mob_position,=lo_cation.plot(mob_long,mob_lat,'g', linewidth=2)
my_position,=lo_cation.plot(my_long,my_lat,boat_colour,linewidth=2)

#plot coaslines
for counter in range(0,len(coast_lats)):
    line_lats=coast_lats[counter]
    line_longs=coast_longs[counter]
    coast_lines=lo_cation.plot(line_longs,line_lats, 'y', linewidth=2)
    


for counter in range(0,len(waypoints_names)):                                                # <--
    lo_cation.annotate(waypoints_lables[counter],(waypoints_longs[counter],waypoints_lats[counter]),color='w') # <--

lo_cation.set_title ("Location", fontsize=18,color='w')
lo_cation.set_ylabel("Lat", fontsize=14,color='w')
lo_cation.set_xlabel("Long", fontsize=14,color='w')
lo_cation.tick_params(labelsize=10,color='w')
lo_cation.grid(True, which='both', color='0.65',linestyle='-')
fig1.subplots_adjust(hspace = 0,bottom=.15, left=.11, right=.95, top=.88)

loc_canvas = FigureCanvasTkAgg(fig1, master=dialcanvas)
loc_canvas.get_tk_widget().place(x=Ccx-(Nx*my_dpi/2),y=Ccy-(Nx*my_dpi/2))
loc_canvas.draw()



#12 charts on the "Data" tab

#True wind speed, True wind direction, Temperature and atmopspheric pressure charts (Pane 1 of data tab)
fig3 = Figure(figsize=(3.1,9.5),dpi=my_dpi)
tw_peed = fig3.add_subplot(411)
tw_ngl = fig3.add_subplot(412,sharex=tw_peed)
temp_eg = fig3.add_subplot(413,sharex=tw_peed)
press_bar = fig3.add_subplot(414,sharex=tw_peed)

tw_peed.axis([atmitems*physicsupdate,0,0,35])
tw_ngl.axis([atmitems*physicsupdate,0,0,360])
temp_eg.axis([atmitems*physicsupdate,0,0,30])
press_bar.axis([atmitems*physicsupdate,0,920,1050])

li5, = tw_peed.plot(kexv,true_wnd_spd_data, label='TWS knts')
li6, = tw_ngl.plot(kexv,true_wnd_dir_data, label='TW angle')
li7, = temp_eg.plot(kexv,temp_deg_data, label= 'Temp deg')
li8,=  press_bar.plot(kexv,press_mbar_data, label= 'Press Mbar')

tw_peed.legend(loc='upper left')
tw_ngl.legend(loc='upper left')
temp_eg.legend(loc='upper left')
press_bar.legend(loc='upper left')

plt.setp(tw_peed.get_xticklabels(), visible=False)
plt.setp(tw_ngl.get_xticklabels(), visible=False)
plt.setp(temp_eg.get_xticklabels(), visible=False)
plt.setp(press_bar.get_xticklabels(), visible=True)
tw_peed.tick_params(labelsize=10)
tw_ngl.tick_params(labelsize=10)
temp_eg.tick_params(labelsize=10)
press_bar.tick_params(labelsize=10)
press_bar.set_xlabel("Time in seconds", fontsize=10)
fig3.subplots_adjust(hspace = .13,bottom=.15, left=.2, right=.95, top=.95)
tw_peed.grid(True, which='both', color='0.65',linestyle='-')
tw_ngl.grid(True, which='both', color='0.65',linestyle='-')
temp_eg.grid(True, which='both', color='0.65',linestyle='-')
press_bar.grid(True, which='both', color='0.65',linestyle='-')

atm_canvas = FigureCanvasTkAgg(fig3, master=datapane1)
atm_canvas.get_tk_widget().place(x=0,y=0)
atm_canvas.draw()
plt.show(block=False)


#Pitch, roll, speed and KE charts (Pane 2 of data tab)
fig2 = Figure(figsize=(3.1,9.5),dpi=my_dpi)
sp_eed = fig2.add_subplot(411)
ro_ll = fig2.add_subplot(412,sharex=sp_eed)
pi_tch = fig2.add_subplot(413,sharex=sp_eed)
ke_nergy = fig2.add_subplot(414,sharex=sp_eed)

sp_eed.axis([keitems*physicsupdate,0,0,10])
ro_ll.axis([keitems*physicsupdate,0,-40,40])
pi_tch.axis([keitems*physicsupdate,0,-15,15])
ke_nergy.axis([keitems*physicsupdate,0,0,20000])


li, = ro_ll.plot(kexv,roll_data, label='Roll deg')
li2, = pi_tch.plot(kexv,pitch_data, label='Pitch Deg')
li3, = sp_eed.plot(kexv,speed_data, label= 'Speed Knots')
li4,=ke_nergy.plot(kexv,ke_data, label= 'KE Joules')

sp_eed.legend(loc='upper left')
ro_ll.legend(loc='upper left')
pi_tch.legend(loc='upper left')
ke_nergy.legend(loc='upper left')

plt.setp(sp_eed.get_xticklabels(), visible=False)
plt.setp(ro_ll.get_xticklabels(), visible=False)
plt.setp(pi_tch.get_xticklabels(), visible=False)
plt.setp(ke_nergy.get_xticklabels(), visible=True)
sp_eed.tick_params(labelsize=10)
ro_ll.tick_params(labelsize=10)
pi_tch.tick_params(labelsize=10)
ke_nergy.tick_params(labelsize=10)
ke_nergy.set_xlabel("Time in seconds", fontsize=10)
fig2.subplots_adjust(hspace = .13,bottom=.15, left=.2, right=.95, top=.95)
sp_eed.grid(True, which='both', color='0.65',linestyle='-')
ro_ll.grid(True, which='both', color='0.65',linestyle='-')
pi_tch.grid(True, which='both', color='0.65',linestyle='-')
ke_nergy.grid(True, which='both', color='0.65',linestyle='-')

ke_canvas = FigureCanvasTkAgg(fig2, master=datapane2)
ke_canvas.get_tk_widget().place(x=0,y=0)
ke_canvas.draw()
plt.show(block=False)















###Main routines start here!###

#Main function for getting all the navigational data and returning it in list form
def nav_data_grab():
    global Mag_dec
    global soft_correct
    global waypoints_lats
    global waypoints_longs
    global next_waypoint_name
    nancatcher=False
    
    nav_data_list=[0]*20
    nav_data_list[0]=['Magnetic soft correct', soft_correct]
    nav_data_list[1]=['Magnetic Bearing', round(compass.get_currentValue(),0)]
    nav_data_list[2]=['Magnetic Declination', Mag_dec]

    #There has been a problem with the returning of NaNs from the GPS module
    #The simplest way to remove them is at source.  This section iterates until tracks are found
    #So the five GPS values (Track, speed, Lat, Long and Time) are cleared here

    while nancatcher==False:
        nav_data_list[3]=['GPS track', round(gpsd.fix.track)]
        nav_data_list[4]=['GPS speed kph', round(gpsd.fix.speed,2)]
        nav_data_list[5]=['GPS lat decimal', gpsd.fix.latitude]
        nav_data_list[6]=['GPS long decimal', gpsd.fix.longitude]
        nancatcher=True
        for chknan in range (3,6):
            if math.isnan(nav_data_list[chknan][1])==True:
                print "GPS fix lost - Refixing"
                nancatcher=False

                
                    
    nav_data_list[7]=['GPS time', gpsd.fix.time]
    nav_data_list[8]=['Roll value degrees', roll.get_currentValue()]      
    nav_data_list[9]=['Pitch value degrees', pitch.get_currentValue()]         
    nav_data_list[10]=['Longitudinal acceleration g', accelerometer.get_xValue()]
    nav_data_list[11]=['Lateral acceleration g', accelerometer.get_yValue()]
    nav_data_list[12]=['Vertical acceleration g', accelerometer.get_zValue()]
    waypoint_tag=next_waypoint_name.get()
    waypoint_number=int(waypoint_tag[0:2])
    nav_data_list[13]=['Next waypoint name', waypoint_tag]
    nav_data_list[14]=['Next waypoint list position',waypoint_number]
    nav_data_list[15]=['Lat of next waypoint', float(waypoints_lats[waypoint_number])]
    nav_data_list[16]=['Long of next waypoint', float(waypoints_longs[waypoint_number])]
    next_waypoint_range=dmsmodule.range_sphere(nav_data_list[5][1], nav_data_list[6][1], nav_data_list[15][1], nav_data_list[16][1],'nm')
    next_waypoint_bearing=dmsmodule.calculate_initial_compass_bearing(nav_data_list[5][1], nav_data_list[6][1], nav_data_list[15][1], nav_data_list[16][1])

    nav_data_list[17]=['Range to next waypoint', next_waypoint_range]
    nav_data_list[18]=['Bearing to next waypoint', next_waypoint_bearing]

    return nav_data_list

  

#Simple counter function for simulation mode
def simtick(simplace,table):
    simplace=simplace+1
    if simplace==len(table):
        simplace=1  
    return simplace

#Function for calculating the raduis for a "Square" dial
def square_needle(bbearing,rradia,Cnll):
#Work out radius for "square" compass
    if bbearing>45 and bbearing <135 or bbearing>225 and bbearing <315:
        Lnll=Cnll*(1/math.sin(rradia))
    else:
        Lnll=Cnll*(1/math.cos(rradia))
    
    return abs(Lnll)

   

#Function for updating the compass and tracking needle
def com_needle(New_bearing,Ccx,Ccy,Cnl,Tnl,Target_bearing,Target_selection):
    global compass_needle
    global tracking_needle
    radia=math.radians(New_bearing)
    Lnl=square_needle(New_bearing,radia,Cnl)
    
    Cnx=round(Ccx+Lnl*math.sin(radia))
    Cny=round(Ccy-Lnl*math.cos(radia))  #Note, because of the arse-wise coordinate system the Y term has to be inverted
    dialcanvas.coords(compass_needle,Ccx,Ccy,Cnx,Cny)
    radia=math.radians(float(Target_bearing))
    if Target_selection==0:
        Tnl=0
    Lnl=square_needle(float(Target_bearing),radia,Tnl)
    Cnx=round(Ccx+Lnl*math.sin(radia))
    Cny=round(Ccy-Lnl*math.cos(radia))
    dialcanvas.coords(tracking_needle,Ccx,Ccy,Cnx,Cny)

#Function for updating the compass and tracking needle
def per_wind_needle(app_angle,true_angle,Perx,Pery,Pwol,Pwil):
    global per_app_needle
    global per_true_needle
    radia=math.radians(app_angle)
        
    Wrxo=round(Perx+Pwol*math.sin(radia))
    Wryo=round(Pery-Pwol*math.cos(radia)) 
    Wrxi=round(Perx+Pwil*math.sin(radia))
    Wryi=round(Pery-Pwil*math.cos(radia))
    performance_canvas.coords(per_app_needle,Wrxi,Wryi,Wrxo,Wryo)

    

    radia=math.radians(true_angle)
        
    Wrxo=round(Perx+Pwol*math.sin(radia))
    Wryo=round(Pery-Pwol*math.cos(radia)) 
    Wrxi=round(Perx+Pwil*math.sin(radia))
    Wryi=round(Pery-Pwil*math.cos(radia))
    performance_canvas.coords(per_true_needle,Wrxi,Wryi,Wrxo,Wryo)

#Function for updating the atmospheric lables
def per_atm_update(Appspeed,Truespeed,Tempdeg,Pressmbar):
    global App_Spd
    global True_Spd
    global Temp_deg
    global Press_mbar
    App_Spd.set(round(Appspeed,1))
    True_Spd.set(round(Truespeed,1))
    Temp_deg.set(int(Tempdeg))
    Press_mbar.set(int(Pressmbar))
        
        
        



#Functon for updating the speed needle
def speed_needle(New_speed,Spx,Spy,Spl,back_ground_colour,needle_colour,arrowhead):
    global sppeed_needle
    radia=math.radians(New_speed*20.25+225)
    Snx=round(Spx+Spl*math.sin(radia))
    Sny=round(Spy-Spl*math.cos(radia))  #Note, because of the arse-wise coordinate system the Y term has to be inverted
    performance_canvas.coords(sppeed_needle,Spx,Spy,Snx,Sny)

#Functon for updating the speed needle
def upwind_needle(Upwind_speed,Spx,Spy,Spl,back_ground_colour,needle_colour,arrowhead):
    global uppwind_needle
    radia=math.radians(Upwind_speed*20.25+225)
    Snx=round(Spx+Spl*math.sin(radia))
    Sny=round(Spy-Spl*math.cos(radia))  #Note, because of the arse-wise coordinate system the Y term has to be inverted
    performance_canvas.coords(uppwind_needle,Spx,Spy,Snx,Sny)



#Function for updating the peripheral artifical horizon
def peripheral_artifical_needle(roll_angle,pitch_angle,Ccx,Ccy,pahr,Dh):
    global peripheral_artificial_horizon
    radia1=math.radians(roll_angle+90)
    radia2=math.radians(roll_angle-90)

    #Calculate line angle based on roll angle
    #Note, that because the PAH is the inverse of the actual roll angle, Plusses have been used for the Y coordinates which would usually show minuses
    pahx1=round(Ccx+pahr*math.sin(radia1))
    pahy1=round(Ccy+pahr*math.cos(radia1))
    pahx2=round(Ccx+pahr*math.sin(radia2))
    pahy2=round(Ccy+pahr*math.cos(radia2))

    #Calculate line elevation based on pitch angle
    #We assume the display is a sphere, of radius Dh/2 (250) pixles
    #We then project perpendicular from the plane attatched to the boat
    #Where this intersects with the pseudo sphere, we draw the horison line
    
    pseudo_sphere_radius=Dh/2
    ptheta=math.radians(pitch_angle)

    vertical_offset=pseudo_sphere_radius*math.sin(ptheta)
    pahy1=pahy1+vertical_offset
    pahy2=pahy2+vertical_offset  
    dialcanvas.coords(peripheral_artificial_horizon,pahx1,Dh,pahx1,pahy1,pahx2,pahy2,pahx2,Dh)





#Function for updating the data table (lat, long, course, time)
def data_table(process_nav_data,disp_lat,disp_long,disp_course,disp_time,next_waypoint_range,next_waypoint_bearing):
    disp_lat.set('lat ' +process_nav_data[5][1])
    disp_long.set('long ' +process_nav_data[6][1])
    disp_course.set('CMG %d' %(process_nav_data[3][1]))
    next_waypoint_range.set('Range ' +process_nav_data[13][1]+' Nm')
    next_waypoint_bearing.set('Bearing ' +process_nav_data[14][1]+process_nav_data[15][1])
    disp_time.set(process_nav_data[7][1])
    dataframe.update()

#Function to update roll data history
def pitch_roll_data_history(pitch_data,roll_data,roll_value,pitch_value):
    global pitchandroll
    global li
    global li2
    pitch_data.pop()
    pitch_data.insert(0,pitch_value)
    roll_data.pop()
    roll_data.insert(0,roll_value)
    li.set_ydata(roll_data)
    li2.set_ydata(pitch_data)

#Function to update speed and KE data history
def speed_data_history(speed_data,speed_value,ke_data,ke_value):
    global sp_eed
    global ke_nergy
    global li3
    global li4
    speed_data.pop()                    #Remove last value from list
    speed_data.insert(0,speed_value)    #Add new value to list
    ke_data.pop()                    #Remove last value from list
    ke_data.insert(0,ke_value)    #Add new value to list
    li3.set_ydata(speed_data)
    li4.set_ydata(ke_data)

#Function to update atmpspheric data (metmast) history
def atmospheric_data_history(spd_val,dir_val,temp_val,press_val):
    global sp_eed
    global ke_nergy
    global li5
    global li6
    global li5
    global li6
    global true_wnd_spd_data
    global true_wnd_dir_data
    global temp_deg_data
    global press_mbar_data
    true_wnd_spd_data.pop()                    #Remove last value from list
    true_wnd_spd_data.insert(0,spd_val)        #Add new value to list
    true_wnd_dir_data.pop()                    
    true_wnd_dir_data.insert(0,dir_val)        
    temp_deg_data.pop()
    temp_deg_data.insert(0,temp_val)        
    press_mbar_data.pop()                   
    press_mbar_data.insert(0,press_val)     
    li5.set_ydata(true_wnd_spd_data)
    li6.set_ydata(true_wnd_dir_data)
    li7.set_ydata(temp_deg_data)
    li8.set_ydata(press_mbar_data)

    

#Function to update location data history
def location_data_history(his_lat,his_long,curlat,curlong,max_storage,heading,roll):
    global lo_cation
    global curr_position
    global mob_position
    global my_position
    global lo_cation_scale
    his_lat.append(curlat)
    his_long.append(curlong)

    if len(his_lat)>max_storage:
        his_lat.pop(0)
        his_long.pop(0)
    
    curr_position.set_xdata(his_long)            
    curr_position.set_ydata(his_lat)

    #Draw the "My position" marker
    mark_points=dmsmodule.plot_marker(curlat,curlong,.2,lo_cation_scale,2,heading,roll)
    my_lat=mark_points[0]
    my_long=mark_points[1]
    my_position.set_xdata(my_long)
    my_position.set_ydata(my_lat)

#Iterate until GPS location is found

lasttime=round(time.time(),pr)
gctime=round(time.time())
counter=0


basic_nav_data=nav_data_grab()      #Get basic navigation data
O_p_n_d=dmsmodule.nav_data_process(basic_nav_data,MTC,simmode, simtable,simcount,Cbt,Spd,Vad,sim_course_data,lasttime) #Process navigation data for display
process_nav_data=dmsmodule.nav_data_process(basic_nav_data,MTC,simmode, simtable,simcount,Cbt,Spd,Vad,sim_course_data,lasttime) #Process navigation data for display

print 'Searching for GPS fix'
while len(process_nav_data[5][1])<4:
    process_nav_data=dmsmodule.nav_data_process(basic_nav_data,MTC,simmode, simtable,simcount,Cbt,Spd,Vad,sim_course_data,lasttime) #Process navigation data for display

print 'GPS fix achieved'
lastlat=process_nav_data[16][1]
lastlong=process_nav_data[17][1]

print 'Time',disp_time.get()
print 'Starting lat DMS',process_nav_data[5][1]
print 'Starting long DMS',process_nav_data[6][1]
print 'lat decimal',process_nav_data[16][1]
print 'long decimal',process_nav_data[17][1]




#Man overboard function - handles initial MOB and also resets when called from the "MOB_RESET" function
def MOB_handle():

    global process_nav_data
    global disp_time
    global disp_lat
    global disp_long
    global waypoints_names
    global waypoints_lats
    global waypoints_longs
    global next_waypoint_name
    global mob_lat
    global mob_long
    global scale_choice
    global scale_pos
    global lo_cation
    global lo_cation_scale
    global disp_scale
    global tripometer
    global log_name
    global MOB_reset


    if MOB_reset==1:
        print '***Man Overboard***'
        scale_pos=0
        next_waypoint_name.set(waypoints_names[1])
        waypoints_lats[1]=process_nav_data[16][1]
        waypoints_longs[1]=process_nav_data[17][1]
    else:
        print '***MOB reset selected***'
        scale_pos=5


    print 'Time',disp_time.get()
    print 'Lat DMS',disp_lat.get()
    print 'long DMS',disp_long.get()
    print 'lat decimal',process_nav_data[16][1]
    print 'long decimal',process_nav_data[17][1]

    lo_cation_scale=scale_choice[scale_pos]
    mark_points=dmsmodule.plot_marker(waypoints_lats[1],waypoints_longs[1],.5,lo_cation_scale,1,process_nav_data[0][1],0)

    mob_lat=mark_points[0]
    mob_long=mark_points[1]

    mob_position.set_xdata(mob_long)
    mob_position.set_ydata(mob_lat)
    lo_cation_axis=dmsmodule.location_axis(process_nav_data[16][1],process_nav_data[17][1],4,3,lo_cation_scale)
    lo_cation.axis(lo_cation_axis)
    disp_scale.set('Chart ' +str(round((lo_cation_scale*Nx/Ny),2))+' x '+ str(lo_cation_scale)+' Nm')
    loc_canvas.draw()
    visualframe.update()

    data_log(tripometer,log_name,process_nav_data,1)
    

#Man overboard reset function
def MOB_RESET():
    global MOB_reset
    MOB_reset=0
    MOB_handle()
    
    


#Draw Man overboard button
mobphoto=PhotoImage(file="Man overboard.gif")
MOB_button=Button(CW, command = MOB_handle)
MOB_button.config(bg='yellow')
MOB_button.config(image=mobphoto,width="800",height="38")
MOB_button.place(x=0, y=Taby+30)

#Draw Man overboard reset button
MOB_reset_button=Button(keyframe, text="Reset MOB",command = MOB_RESET)
MOB_reset_button.config(bg='orange',font=('helvetica', 16))
MOB_reset_button.config(width="8",height="1")
MOB_reset_button.place(x=20, y=160)

#Function for chart zooming in
def zoom_in():
    global scale_pos
    scale_pos=scale_pos-1
    zoom_draw()
   

def zoom_out():
    global scale_pos  
    scale_pos=scale_pos+1
    zoom_draw()


def zoom_draw():
    global lo_cation
    global lo_cation_scale
    global scale_choice
    global scale_pos
    global disp_scale
    global visualframe
    if scale_pos<0:
        scale_pos=0
    if scale_pos>len(scale_choice):
        scale_pos=len(scale_choice)

    lo_cation_scale=scale_choice[scale_pos]
    disp_scale.set('Chart ' +str(round((lo_cation_scale*Nx/Ny),2))+' x '+ str(lo_cation_scale)+' Nm')
  
    lo_cation_axis=dmsmodule.location_axis(process_nav_data[16][1],process_nav_data[17][1],4,3,lo_cation_scale)
    lo_cation.axis(lo_cation_axis)

    loc_canvas.draw()
    visualframe.update()
    

#Setup chart zoom buttons
zoomphoto1=PhotoImage(file="Zoom in.gif")
zoom_in_button=Button(dialcanvas, command = zoom_in)
zoom_in_button.config(image=zoomphoto1,width="38",height="38")
zoom_in_button.place(x=250, y=500)

disp_scale=StringVar()
disp_scale.set('Chart ' +str(round((lo_cation_scale*Nx/Ny),2))+' x '+ str(lo_cation_scale)+' Nm')
disp_scale_label=Label(dialcanvas,textvariable=disp_scale,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
disp_scale_label.place(x=300,y=520)


zoomphoto2=PhotoImage(file="Zoom out.gif")
zoom_out_button=Button(dialcanvas, command = zoom_out)
zoom_out_button.config(image=zoomphoto2,width="38",height="38")
zoom_out_button.place(x=510, y=500)




#Function for resetting the tripometer
def reset_trip():
    global tripometer
    global disp_trip
    tripometer=0
    disp_trip.set('Distance ' +str(tripometer)+' Nm')

def trip_calculate(curlat,curlong,lastlat,lastlong):
    global tripometer
    global disp_trip
    tripometer=tripometer+dmsmodule.range_sphere(curlat,curlong,lastlat,lastlong,'nm')
    disp_trip.set('Distance ' +str(round(tripometer,2))+' Nm')    

    
#Setup reset tip button and lable
disp_trip=StringVar()
disp_trip.set('Distance ' +str(tripometer)+' Nm')
trip_label=Label(dataframe,textvariable=disp_trip,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
trip_label.place(x=10,y=275)

reset_trip_button=Button(keyframe,text='Reset trip', command = reset_trip)
reset_trip_button.config(bg='green',font=('helvetica', 16))
reset_trip_button.config(width="8",height="1")
reset_trip_button.place(x=20, y=10)

#function for saving the data to a log file
def data_log(tripometer,log_name,process_nav_data,MOB):

    Nav_log_object=open(log_name, "a")

    #Write MOB data
    if MOB==1:
        Nav_log_object.write('***Man Overboard recorded!***\n')
    

    Nav_log_object.write(process_nav_data[7][1]+','
                         +str(process_nav_data[16][1])+','
                         +str(process_nav_data[17][1])+','
                         +str(process_nav_data[0][1])+','
                         +str(process_nav_data[3][1])+','
                         +str(process_nav_data[4][1])+','
                         +str(process_nav_data[9][1])+','
                         +str(process_nav_data[8][1])+','
                         +str(tripometer)+'\n')

    Nav_log_object.close()



#Main loop for updating GUI



while True:
    

    nowtime=round(time.time(),pr)     
    counter=counter+1
    ud=0
    simcount=simtick(simcount,simtable) #Call simulation counter function
    basic_nav_data=nav_data_grab()      #Get basic navigation data
    process_nav_data=dmsmodule.nav_data_process(basic_nav_data,MTC,simmode, simtable,simcount,Cbt,Spd,Vad,sim_course_data,nowtime) #Process navigation data for display
    
    #Check for updates to compass - updates if anything has changed

    if process_nav_data[0][1]<>O_p_n_d[0][1]:
        ud=1
        com_needle(process_nav_data[0][1],Ccx,Ccy,Cnl,Tnl, process_nav_data[14][1],basic_nav_data[14][1])  #Update compass needle
    if process_nav_data[8][1]<>O_p_n_d[8][1]:
        ud=1
        peripheral_artifical_needle(process_nav_data[8][1],process_nav_data[9][1],Ccx,Ccy,pahr,Dh)    
    if ud==1:
        dialcanvas.update()
        ud=0

    #Update performance tab as required
    if process_nav_data[4][1]<>O_p_n_d[4][1]:
        ud=1
        speed_needle(process_nav_data[4][1],Spx,Spy,Spl,back_ground_colour,needle_colour,arrowhead)  #Update speed needle
        
    if nowtime-windtmr>windupdate:
        ud=1
        up_sp=processed_met_data[11][1]
        Uws.set(up_sp)
        upwind_needle(up_sp,Spx,Spy,Spl,back_ground_colour,upwind_colour,arrowhead)  #Update upwind needle
        per_wind_needle(processed_met_data[1][1],processed_met_data[6][1],Perx,Pery,Pwol,Pwil) #Update wind needles
        per_atm_update(processed_met_data[0][1],processed_met_data[7][1],processed_met_data[2][1],processed_met_data[3][1])
       
        windtmr=round(time.time(),pr)

    if ud==1:
        performance_canvas.update()
    
    #Update graphs in KE frame data as required
    if nowtime-phytmr>physicsupdate:
        ls=process_nav_data[4][1]
        lk=.5*boat_mass*(ls*.5144)**2    
        pitch_roll_data_history(pitch_data,roll_data,process_nav_data[8][1],process_nav_data[9][1])
        speed_data_history(speed_data,ls,ke_data,lk)
        ke_canvas.draw()
        phytmr=round(time.time(),pr)

    #Update graphs in atmospheric frame as required
    if nowtime-atmtmr>atmupdate:
        atmospheric_data_history(processed_met_data[0][1],processed_met_data[1][1],processed_met_data[2][1],processed_met_data[3][1])
        atm_canvas.draw()
        atmtmr=round(time.time(),pr)


    #Update data table
    if len(process_nav_data[7][1])>1:
        data_table(process_nav_data,disp_lat,disp_long,disp_course,disp_time,next_waypoint_range,next_waypoint_bearing)

    #Check for hard-wired MOB press.  Note, MOB is delieratly hard wired as fail safe and returns 0 if pressed
        if MOB_reset==1:
            if GPIO.input(4)==1:
                MOB_RESET()

        if MOB_reset==0:
            if GPIO.input(4)==0:
                MOB_reset=1
                MOB_handle()


    #Update location chart
    if nowtime-navtmr>navchartupdate:
        print 'Time',time.ctime()
        print 'Cycles ',counter
        print 'Distance ' +str(tripometer)+' Nm'
        navtmr=round(time.time(),pr)
        location_data_history(his_lat,his_long,process_nav_data[16][1],process_nav_data[17][1],max_storage,process_nav_data[0][1],process_nav_data[8][1])
        lo_cation_axis=dmsmodule.location_axis(process_nav_data[16][1],process_nav_data[17][1],Nx,Ny,lo_cation_scale)
        trip_calculate(process_nav_data[16][1],process_nav_data[17][1],lastlat,lastlong)

        data_log(tripometer,log_name,process_nav_data,0)

        lo_cation.axis(lo_cation_axis)
        loc_canvas.draw()
        visualframe.update()
        lastlat=process_nav_data[16][1]
        lastlong=process_nav_data[17][1]
        counter=0

    
       

    O_p_n_d=process_nav_data
    
    
    

    
    
 
 



CW.mainloop()


