# -*- coding: utf-8 -*-
#Olly Epsom May 2017
#Slightly more complex software to get Metmast data, and also calculate true wind speed
#delivers the following infomation when it receives the following commands
#Outbound request       Inbound data
#   1                   Windspeed in Knots (Pre calibrated)
#   2                   Smoothed apparent wind angle in degrees
#   3                   Wind colour (Red or Green)
#   4                   Windbearing (0-180).  To be used with Wind Colour eg "Red 55"
#   5                   Atmospheric pressure in Mbar
#   6                   Temperature in degrees (Note, will not go negative so dont rely on it in winter)
#   7                   Wether sensor health 
#   8                   All data in a stream of tab seperated strings
#   9                   basic 4 sets of measurement data in a single string

#Note this software will eventually be integrated into the Nav-Attack system 5
#Note that metmast Bluetooth HC 05 module is 98:D3:36:00:BD:3B
#If you are using another module you must change the adress in this programme.

boat_velocity=[4,30]             #Boat speed in Knots and course in degrees
raw_met_data = []                #Metmast data
processed_met_data=[0,0,0,0,0]
true_wind_velocity=[0,0]         #True wind speed in knots and course in degrees
dir_correct=0                    #Soft-correct for the wind bearing in degrees
spd_correct=1                    #Soft -correct for the wind speed in factors

sendnum=0

import bluetooth
import time
import dmsmodule


#Connect with metmast
print 'Connecting to Metmast via Bluetooth'
bd_addr = '98:D3:36:00:BD:3B' 
port = 1
MetMast = bluetooth.BluetoothSocket (bluetooth.RFCOMM)
MetMast.connect((bd_addr,port))
print 'Got this far, press Ctrl-C to quit'







while 1:
    sendnum=sendnum+1
    if sendnum>9:
        sendnum=1

    #tosend = str(sendnum)
    tosend='8'
    print 'sending',tosend
    MetMast.send(tosend)
    time.sleep(.1)

    try:
        buffer = MetMast.recv(4096)
        inbounddata=buffer
        raw_met_data=inbounddata.split("\t")
        if len(raw_met_data)>1:
            processed_met_data=dmsmodule.met_mast_correct(raw_met_data,dir_correct,spd_correct)
        print 'Receiving',processed_met_data

        time.sleep(1)
    except:
        print 'Bummer dude'

        
