#!/usr/bin/python

#Note, This version has been re-written to be
#      Clearer to read, and uses lists to share data
#      rather than many individual values.
#      Includes GPS/Yocto Nav/Attack system with waypoints
#      Includes charting
# -*- coding: utf-8 -*-

print ('importing data')

import os,sys
# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("..","..","Sources"))
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

#We are using GPIO 4 as the input for the hard wired MOB button.
#I have always thought GPIO 4 is the lucky pin!

GPIO.setmode(GPIO.BCM)
GPIO.setup(4,GPIO.IN)



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
com_text_size = 50
s_text_size = 30
back_ground_colour="#321000"
dial_colour="red"
needle_colour="red"
tracking_colour="yellow"
text_colour="#000fff000"
text_font="Helvetica"
horizon_colour='#000000333'
horizon_fill="gray50"
my_dpi=80 #DPI of display, used by charts
boat_colour='m'


Disp_bearing=0

Wsx=1000    #window size x
Wsy=800     #window size y
Dh=470      #height of dial canvas
Ccx=Wsx/2   #Compass centre x
Ccy=250     #Compass centre y
Cd=300      #Compass diameter
Cnl=195     #Compass Needle length
Tnl=150     #Tracking needle length
Cnx=Ccx     #Initial needle end x
Cny=Ccy-Cnl #Initial needle end y
Spx=230     #Speed dial x
Spy=Ccy     #Speed dial y
Spd=336     #Speed dial diameter
Spl=180     #Speed dial length
Snx=Spx     #Initial speed dial x
Sny=Spy+Cnl #Initial speed dial y
Vax=Wsx-210 #Vario dial x
Vay=Ccy     #Vario dial y
Vad=336     #Vario dial diameter
Val=180     #Vario dial length
Vnx=Vax+Val #Initial vario x
Vny=Vay     #Initial vario y
MOB_reset=0 #Man Overboard button not pressed

#Perihpheral artifical horizon coordinates
pahr=800
pahx1=Ccx-pahr
pahx2=Ccx+pahr
pahy1=Ccy
pahy2=Ccy


yn="Y3DMK001-5558D"             #Name of my Yocto3D device
bl=['','']
basic_nav_data=[bl]*20          #Blank navigation data list
process_nav_data=basic_nav_data #Processed navigation data list
O_p_n_d=[0]*20                  #Used for anti flicker
soft_correct=8                  #Soft correction for compass - i.e, its been installed on the wonk

time_data=range(100,-1,-1)      #Array of last 100 seconds
roll_data=[0]*100               #Array of historical roll data
pitch_data=[0]*100              #Array of historical pitch data
speed_data=[0]*100              #Array of historical speed data
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
log_name='/root/Navigation log files/'+str(time.ctime())+'.csv'
Nav_log_object=open(log_name, "a")
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
CW.title('Navigation and Attack system 3.0 David Ben-Gurion')

#Setup dial frame
dialcanvas = Canvas(CW, width=Wsx, height=Dh)
dialcanvas.pack()
background_box=dialcanvas.create_rectangle(0, 0, Wsx, Dh, fill=back_ground_colour)
dashboard_image_day  = PhotoImage(file = 'dashboardday.gif')
dashboard_image_night = PhotoImage(file = 'dashboardnight.gif')
dashboard_background=dialcanvas.create_image(Ccx,Ccy, image=dashboard_image_day)
peripheral_artificial_horizon=dialcanvas.create_polygon(0,Dh,pahx1,pahy1,pahx2,pahy2,pahx2,Dh,fill=horizon_colour, stipple=horizon_fill,width=4)


Compass_rose=dialcanvas.create_oval(Ccx-(Cd/2),Ccy-(Cd/2),Ccx+(Cd/2),Ccy+(Cd/2), outline=dial_colour,fill=back_ground_colour, width=10)
arrowhead = [32,40,12]
dialcanvas.arrowshape = arrowhead
Speed_rose=dialcanvas.create_arc((Spx-(Spd/2),Spy-(Cd/2),Spx+(Spd/2)+30,Spy+(Cd/2)),start=90, extent=180, outline=dial_colour,fill=back_ground_colour, width=10)
Vario_rose=dialcanvas.create_arc((Vax-(Vad/2)-30,Vay-(Cd/2),Vax+(Vad/2),Vay+(Cd/2)),start=-90, extent=180, outline=dial_colour,fill=back_ground_colour, width=10)

#Create needle objects
compass_needle=dialcanvas.create_line(Ccx,Ccy,Cnx,Cny, fill=needle_colour, width=4, arrow="last",arrowshape=arrowhead)
tracking_needle=dialcanvas.create_line(Ccx,Ccy,Cnx,Cny, fill=tracking_colour, width=3, arrow="last",arrowshape=arrowhead)
sppeed_needle=dialcanvas.create_line(Spx,Spy,Snx,Sny, fill=needle_colour, width=4, arrow="last",arrowshape=arrowhead)
vaario_needle=dialcanvas.create_line(Vax,Vay,Vnx,Vny, fill=needle_colour, width=4, arrow="last",arrowshape=arrowhead)




#Setup Magnetic Bearing Label
Cbt=StringVar()
Cbt.set('')
Bear_label_text = StringVar()
Bear_label_text.set('-Magnetic Bearing-')      
Bear_Val=Label(dialcanvas,textvariable=Cbt,bg=back_ground_colour,fg=text_colour,font=(text_font,com_text_size))
Bear_Label=Label(dialcanvas,textvariable=Bear_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Bear_Val.place(x=Ccx-50,y=195)
Bear_Label.place(x=Ccx-70, y=265)

#Setup Speed lable
Spd=StringVar()
Spd.set('')
Spd_name=StringVar()
Spd_label_text = StringVar()
Spd_label_text.set('Knots')
Spd_name.set('Speed')
Spd_name_Label=Label(dialcanvas,textvariable=Spd_name,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Spd_Val=Label(dialcanvas,textvariable=Spd,bg=back_ground_colour,fg=text_colour,font=(text_font,s_text_size))
Spd_Label=Label(dialcanvas,textvariable=Spd_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Spd_Val.place(x=Spx-52,y=220)
Spd_Label.place(x=Spx-45, y=265)
Spd_name_Label.place(x=Spx-45, y=200)

#Setup Vario lable
Vad=StringVar()
Vad.set('0.0')
Vad_name=StringVar()
Vad_label_text = StringVar()
Vad_label_text.set('M/s2')
Vad_name.set('Vario')
Vad_name_Label=Label(dialcanvas,textvariable=Vad_name,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Vad_Val=Label(dialcanvas,textvariable=Vad,bg=back_ground_colour,fg=text_colour,font=(text_font,s_text_size))
Vad_Label=Label(dialcanvas,textvariable=Vad_label_text,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
Vad_Val.place(x=Vax-5,y=220)
Vad_Label.place(x=Vax-5, y=265)
Vad_name_Label.place(x=Vax-5, y=200)







#Setup text frames

modeframe = Canvas(CW,width=200, height=Wsy-Dh)
modeframe.place(x=0, y=Dh)

dataframe=Canvas(CW,width=200, height=Wsy-Dh)
dataframe.place(x=Wsx-200, y=Dh)

visualframe=Canvas(CW, width=Wsx-400, height=Wsy-Dh)
visualframe.place(x=200, y=Dh)


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
    dialcanvas.itemconfig(Speed_rose, outline=dial_colour,fill=back_ground_colour)
    dialcanvas.itemconfig(Vario_rose, outline=dial_colour,fill=back_ground_colour)
    dialcanvas.itemconfig(compass_needle, fill=needle_colour)
    dialcanvas.itemconfig(sppeed_needle, fill=needle_colour)
    dialcanvas.itemconfig(vaario_needle, fill=needle_colour)
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

GPS_lat_label=Label(dataframe,textvariable=disp_lat,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
GPS_lat_label.place(x=10,y=175)

GPS_long_label=Label(dataframe,textvariable=disp_long,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
GPS_long_label.place(x=10,y=200)

GPS_course_label=Label(dataframe,textvariable=disp_course,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
GPS_course_label.place(x=10,y=225)

GPS_time_label=Label(dataframe,textvariable=disp_time,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
GPS_time_label.place(x=10,y=250)


#Setup charts

#Main GPS chart
fig1 = Figure(figsize=(4,3),dpi=my_dpi)
lo_cation = fig1.add_subplot(111)
lo_cation.axis(lo_cation_axis)

waypoint_plot = lo_cation.scatter(waypoints_longs,waypoints_lats, marker='o')
curr_position,=lo_cation.plot(his_long,his_lat, 'r',linewidth=3.0)
mob_position,=lo_cation.plot(mob_long,mob_lat,'g', linewidth=2)
my_position,=lo_cation.plot(my_long,my_lat,boat_colour,linewidth=2)

#plot coaslines
for counter in range(0,len(coast_lats)):
    line_lats=coast_lats[counter]
    line_longs=coast_longs[counter]
    coast_lines=lo_cation.plot(line_longs,line_lats, 'b', linewidth=2)
    


for counter in range(0,len(waypoints_names)):                                                # <--
    lo_cation.annotate(waypoints_lables[counter],(waypoints_longs[counter],waypoints_lats[counter])) # <--

lo_cation.set_title ("Location", fontsize=16)
lo_cation.set_ylabel("Lat", fontsize=10)
lo_cation.set_xlabel("Long", fontsize=10)
lo_cation.tick_params(labelsize=10)
lo_cation.grid(True, which='both', color='0.65',linestyle='-')
fig1.subplots_adjust(hspace = 0,bottom=.15, left=.11, right=.95, top=.88)

loc_canvas = FigureCanvasTkAgg(fig1, master=visualframe)
loc_canvas.get_tk_widget().place(x=0,y=0)
loc_canvas.draw()


#Pitch, roll, speed charts
fig2 = Figure(figsize=(3,3),dpi=my_dpi)
sp_eed = fig2.add_subplot(211)
pitchandroll = fig2.add_subplot(212,sharex=sp_eed)
sp_eed.axis([100,0,0,10])
pitchandroll.axis([100,0,-30,30])

li, = pitchandroll.plot(roll_data, label='Roll')
li2, = pitchandroll.plot(pitch_data, label='Pitch')
li3, = sp_eed.plot(speed_data, label= 'Speed')

slegend = sp_eed.legend(loc='upper left')
prlegend = pitchandroll.legend(loc='upper left')


plt.setp(sp_eed.get_xticklabels(), visible=False)
plt.setp(pitchandroll.get_xticklabels(), visible=True)
sp_eed.tick_params(labelsize=10)
pitchandroll.tick_params(labelsize=10)
sp_eed.set_ylabel("Knots", fontsize=10)
pitchandroll.set_ylabel("Pitch and roll", fontsize=10)
pitchandroll.set_xlabel("Time", fontsize=10)
fig2.subplots_adjust(hspace = .13,bottom=.15, left=.15, right=.95, top=.95)
sp_eed.grid(True, which='both', color='0.65',linestyle='-')
pitchandroll.grid(True, which='both', color='0.65',linestyle='-')

ke_canvas = FigureCanvasTkAgg(fig2, master=visualframe)
ke_canvas.get_tk_widget().place(x=340,y=0)
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
    
    nav_data_list=[0]*20
    nav_data_list[0]=['Magnetic soft correct', soft_correct]
    nav_data_list[1]=['Magnetic Bearing', round(compass.get_currentValue(),0)]
    nav_data_list[2]=['Magnetic Declination', Mag_dec]
    nav_data_list[3]=['GPS track', round(gpsd.fix.track)]
    nav_data_list[4]=['GPS speed kph', round(gpsd.fix.speed,2)]
    nav_data_list[5]=['GPS lat decimal', gpsd.fix.latitude]
    nav_data_list[6]=['GPS long decimal', gpsd.fix.longitude]
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


   

#Function for updating the compass and tracking needle
def com_needle(New_bearing,Ccx,Ccy,Cnl,Tnl,Target_bearing,Target_selection,back_ground_colour,needle_colour,arrowhead):
    global compass_needle
    global tracking_needle
    radia=math.radians(New_bearing)
    Cnx=round(Ccx+Cnl*math.sin(radia))
    Cny=round(Ccy-Cnl*math.cos(radia))  #Note, because of the arse-wise coordinate system the Y term has to be inverted
    dialcanvas.coords(compass_needle,Ccx,Ccy,Cnx,Cny)
    radia=math.radians(float(Target_bearing))
    if Target_selection==0:
        Tnl=0
    Cnx=round(Ccx+Tnl*math.sin(radia))
    Cny=round(Ccy-Tnl*math.cos(radia))
    dialcanvas.coords(tracking_needle,Ccx,Ccy,Cnx,Cny)


#Functon for updating the speed needle
def speed_needle(New_speed,Spx,Spy,Spl,back_ground_colour,needle_colour,arrowhead):
    global sppeed_needle
    radia=math.radians(New_speed*18+180)
    Snx=round(Spx+Spl*math.sin(radia))
    Sny=round(Spy-Spl*math.cos(radia))  #Note, because of the arse-wise coordinate system the Y term has to be inverted
    dialcanvas.coords(sppeed_needle,Spx,Spy,Snx,Sny)

#Functon for updating the vario needle
def vario_needle(New_vario,Vax,Vay,Val,back_ground_colour,needle_colour,arrowhead):
    global vaario_needle
    dial_v=abs(New_vario)

    if New_vario==0:
        New_vario=1
    if dial_v<.01:
         dial_v=.01
    dial_v=dial_v*100 


    if New_vario>0:
        dial_v=1*math.log10(dial_v)
    else:
        dial_v=-1*math.log10(dial_v)

    if dial_v>3:
        dial_v=3
    if dial_v<-3:
        dial_v=-3

    radia=math.radians(dial_v*(-180/6)+90)   
    Vnx=round(Vax+Val*math.sin(radia))
    Vny=round(Vay-Val*math.cos(radia))  #Note, because of the arse-wise coordinate system the Y term has to be inverted
    dialcanvas.coords(vaario_needle,Vax,Vay,Vnx,Vny)





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

#Function to update speed data history
def speed_data_history(speed_data,speed_value):
    global sp_eed
    global li3
    speed_data.pop()                    #Remove last value from list
    speed_data.insert(0,speed_value)    #Add new value to list
    li3.set_ydata(speed_data)            

#Function to update speed data history
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




#Man overboard function
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
    next_waypoint_name.set(waypoints_names[1])
    waypoints_lats[1]=process_nav_data[16][1]
    waypoints_longs[1]=process_nav_data[17][1]
    scale_pos=0
    lo_cation_scale=scale_choice[scale_pos]
    mark_points=dmsmodule.plot_marker(waypoints_lats[1],waypoints_longs[1],.5,lo_cation_scale,1,process_nav_data[0][1],0)

    mob_lat=mark_points[0]
    mob_long=mark_points[1]

    mob_position.set_xdata(mob_long)
    mob_position.set_ydata(mob_lat)
    lo_cation_axis=dmsmodule.location_axis(process_nav_data[16][1],process_nav_data[17][1],4,3,lo_cation_scale)
    lo_cation.axis(lo_cation_axis)
    disp_scale.set('Chart ' +str(round((lo_cation_scale*4/3),2))+' x '+ str(lo_cation_scale)+' Nm')
    loc_canvas.draw()
    visualframe.update()

    data_log(tripometer,log_name,process_nav_data,1)
    print '***Man Overboard***'
    print 'Time',disp_time.get()
    print 'Lat DMS',disp_lat.get()
    print 'long DMS',disp_long.get()
    print 'lat decimal',process_nav_data[16][1]
    print 'long decimal',process_nav_data[17][1]


#Draw Man overboard button
mobphoto=PhotoImage(file="Man overboard.gif")
MOB_button=Button(modeframe, command = MOB_handle)
MOB_button.config(bg='yellow')
MOB_button.config(image=mobphoto,width="140",height="38")
MOB_button.place(x=20, y=250)

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
    disp_scale.set('Chart ' +str(round((lo_cation_scale*4/3),2))+' x '+ str(lo_cation_scale)+' Nm')
  
    lo_cation_axis=dmsmodule.location_axis(process_nav_data[16][1],process_nav_data[17][1],4,3,lo_cation_scale)
    lo_cation.axis(lo_cation_axis)

    loc_canvas.draw()
    visualframe.update()
    

#Setup chart zoom buttons
zoomphoto1=PhotoImage(file="Zoom in.gif")
zoom_in_button=Button(visualframe, command = zoom_in)
zoom_in_button.config(image=zoomphoto1,width="38",height="38")
zoom_in_button.place(x=20, y=250)

disp_scale=StringVar()
disp_scale.set('Chart ' +str(round((lo_cation_scale*4/3),2))+' x '+ str(lo_cation_scale)+' Nm')
disp_scale_label=Label(visualframe,textvariable=disp_scale,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
disp_scale_label.place(x=80,y=260)


zoomphoto2=PhotoImage(file="Zoom out.gif")
zoom_out_button=Button(visualframe, command = zoom_out)
zoom_out_button.config(image=zoomphoto2,width="38",height="38")
zoom_out_button.place(x=260, y=250)




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
    disp_trip.set('Distance ' +str(tripometer)+' Nm')    

    
#Setup reset tip button and lable
disp_trip=StringVar()
disp_trip.set('Distance ' +str(tripometer)+' Nm')
trip_label=Label(visualframe,textvariable=disp_trip,bg=back_ground_colour,fg=text_colour,font=(text_font,lab_text_size))
trip_label.place(x=450,y=260)

reset_trip_button=Button(visualframe,text='Reset trip', command = reset_trip)
reset_trip_button.config(bg='green',font=('helvetica', 16))
reset_trip_button.config(width="6",height="1")
reset_trip_button.place(x=340, y=250)

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
    
    #Check for updates to dial graphics

    if process_nav_data[0][1]<>O_p_n_d[0][1]:
        ud=1
        com_needle(process_nav_data[0][1],Ccx,Ccy,Cnl,Tnl, process_nav_data[14][1],basic_nav_data[14][1],back_ground_colour,needle_colour,arrowhead)  #Update compass needle
    if process_nav_data[4][1]<>O_p_n_d[4][1]:
        ud=1
        speed_needle(process_nav_data[4][1],Spx,Spy,Spl,back_ground_colour,needle_colour,arrowhead)  #Update compass needle
    if process_nav_data[10][1]<>O_p_n_d[10][1]:
        ud=1
        vario_needle(process_nav_data[10][1],Vax,Vay,Val,back_ground_colour,needle_colour,arrowhead)
    if process_nav_data[8][1]<>O_p_n_d[8][1]:
        ud=1
        peripheral_artifical_needle(process_nav_data[8][1],process_nav_data[9][1],Ccx,Ccy,pahr,Dh)    
    
    if ud==1:
        dialcanvas.update()
           
    
    #Update graphics
    if nowtime!=lasttime:
        pitch_roll_data_history(pitch_data,roll_data,process_nav_data[8][1],process_nav_data[9][1])
        speed_data_history(speed_data,process_nav_data[4][1])
        ke_canvas.draw()
        lasttime=round(time.time(),pr)

    #Update data table
    if len(process_nav_data[7][1])>1:
        data_table(process_nav_data,disp_lat,disp_long,disp_course,disp_time,next_waypoint_range,next_waypoint_bearing)

    #Check for hard-wired MOB press.  Note, MOB is delieratly hard wired as fail safe and returns 0 if pressed
        if MOB_reset==1:
            if GPIO.input(4)==1:
                MOB_reset=0

        if MOB_reset==0:
            if GPIO.input(4)==0:
                MOB_reset=1
                MOB_handle()


    #Update location chart
    if nowtime-gctime>10:
        
        print 'cycles ',counter
        print 'Distance ' +str(tripometer)+' Nm'
        gctime=round(time.time(),pr)
        location_data_history(his_lat,his_long,process_nav_data[16][1],process_nav_data[17][1],max_storage,process_nav_data[0][1],process_nav_data[8][1])
        lo_cation_axis=dmsmodule.location_axis(process_nav_data[16][1],process_nav_data[17][1],4,3,lo_cation_scale)
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


