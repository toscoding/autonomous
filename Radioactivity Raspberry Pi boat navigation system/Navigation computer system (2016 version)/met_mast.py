# -*- coding: utf-8 -*-
#Olly Epsom May 2017
#Initial software to talk to the Metmast system over bluetooth
#Metmast delivers the following infomation when it receives the following commands
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
sendnum=0

import bluetooth
import time
print 'Connecting to Metmast via Bluetooth'
bd_addr = '98:D3:36:00:BD:3B'
port = 1
sock = bluetooth.BluetoothSocket (bluetooth.RFCOMM)
sock.connect((bd_addr,port))
print 'Got this far, press Ctrl-C to quit'

while 1:
    sendnum=sendnum+1
    if sendnum>9:
        sendnum=1

    #tosend = str(sendnum)
    tosend='9'
    print 'sending',tosend
    sock.send(tosend)
    time.sleep(1)
    buffer = sock.recv(4096)
    print 'Receiving',buffer

    time.sleep(10)
   

        
