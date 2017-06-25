# -*- coding: utf-8 -*-
#Olly Epsom June 2017
#Slightly more complex software to get Metmast data, and also calculate true wind speed
#Uses threads to protype integration with NavAttack5
#Note that metmast Bluetooth HC 05 module is 98:D3:36:00:BD:3B
#If you are using another module you must change the adress in this programme.

boat_velocity=[4,30]             #Boat speed in Knots and course in degrees
raw_met_data = []                #Metmast data
processed_met_data=[0,0,0,0,0]
true_wind_velocity=[0,0]         #True wind speed in knots and course in degrees
dir_correct=0                    #Soft-correct for the wind bearing in degrees
spd_correct=1                    #Soft -correct for the wind speed in factors
tosend='8'                       #Bluetooth request number for metmast
bd_addr = '98:D3:36:00:BD:3B' 
port = 1
MetFitted=True                   #Turn to "False" if MetMast is not available

import bluetooth
import time
import dmsmodule
import threading
MetMast=None

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
          
          if len(raw_met_data)>1:
              processed_met_data=dmsmodule.met_mast_correct(raw_met_data,dir_correct,spd_correct)
          time.sleep(1)



MetGrab = MetThread()   #Create MetMast thread
MetGrab.start()         #Start it up


while True:

    windspeed = processed_met_data[1]
    windangle = processed_met_data[3]
    print windspeed,windangle
    time.sleep(.5)
