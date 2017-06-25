#Example 1 of a program designed to record lat and long points off a google image by mouse clicking
#Used to create rudimentary outline charts for my David Ben Gurion navigation system

import os,sys
import time
from Tkinter import *
import tkSimpleDialog
import math
import tkMessageBox



#Setup display variables
lab_text_size = 12
com_text_size = 50
Disp_bearing=0

Wsx=1800     #window size x
Wsy=1000     #window size y
mapx=1800
mapy=900

lats=[]
longs=[]
line_lats=[]
line_longs=[]
line_code=0

callist=[1,2,3,4,5,6,7,8]
calpoint=0

#Setup GUI objects
CW = Tk()
CW.geometry("1800x1000")
CW.title('Chart lister version 1, Jan Smutts')



#Setup dial frame
mapcanvas = Canvas(CW, width=mapx, height=mapy)
mapcanvas.pack()

dashboard = PhotoImage(file = 'chart.gif')
mapcanvas.create_image(mapx/2,mapy/2, image=dashboard)


#outputting x and y coords to console
def printcoords(event):
    global line_lats
    global line_longs
    global mapcanvas
    
    y=event.y
    x=event.x
    
    mapcanvas.create_rectangle(x-1, y-1, x+1, y+1, width=2,fill="blue")
    mapcanvas.update()
    line_lats.append(y)
    line_longs.append(x)


def New_line_func():
    global line_lats
    global line_longs
    global lats
    global longs
    global line_code

    lats.append(line_lats)
    longs.append(line_longs)
    print lats
    print longs
    line_lats=[]
    line_longs=[]

    

def Delete_line_func():
    global line_lats
    global line_longs
    line_lats=[]
    line_longs=[]

def Convert_and_save_func():
    global lats
    global longs
    global callist


    firstx=callist[0]
    firstlong=callist[1]
    firsty=callist[2]
    firstlat=callist[3]
    secondx=callist[4]
    secondlong=callist[5]
    secondy=callist[6]
    secondlat=callist[7]

    long_per_pixle=(secondlong-firstlong)/(secondx-firstx)
    lat_per_pixle=(secondlat-firstlat)/(secondy-firsty)

    lat_at_origin=firstlat-firsty*lat_per_pixle
    long_at_origin=firstlong-firstx*long_per_pixle


    print lat_per_pixle
    print long_per_pixle
    print lat_at_origin
    print long_at_origin

    #Convert latitude values
    lats_convert=[]

    for i in range(0,len(lats)):
        pix_string=lats[i]
        lat_string=[]
        for z in range (0,len(pix_string)):
            lat_coordinate=pix_string[z]*lat_per_pixle+lat_at_origin
            lat_string.append(lat_coordinate)
        lats_convert.append(lat_string)
    
    #Convert latitude values
    longs_convert=[]

    for i in range(0,len(longs)):
        pix_string=longs[i]
        long_string=[]
        for z in range (0,len(pix_string)):
            long_coordinate=pix_string[z]*long_per_pixle+long_at_origin
            long_string.append(long_coordinate)
        longs_convert.append(long_string)
    


    #convert longitude values




    filename='test2'

    file_type = open(filename+'lats.txt', 'w')
    file_type.write(str(lats_convert)+'\n')
    file_type.close()

    file_type = open(filename+'longs.txt', 'w')
    file_type.write(str(longs_convert)+'\n')
    file_type.close()
        


    

def Calibrate_last_point_func():
    global line_lats
    global line_longs
    global callist
    global mapcanvas
    global calpoint

    if calpoint==0:
        point_num=0
    if calpoint==1:
        point_num=4
    
    lastx=line_longs[-1]
    lasty=line_lats[-1]

    mapcanvas.create_rectangle(lastx-4, lasty-4, lastx+4, lasty+4, width=2)
    

    
    callat=tkSimpleDialog.askfloat("lat","Latitude in decimal")
    callong=tkSimpleDialog.askfloat("long","longitude in decimal") 

    callist[point_num]=lastx
    callist[point_num+1]=callong
    callist[point_num+2]=lasty
    callist[point_num+3]=callat

    calpoint=0
    if point_num==0:
        calpoint=1
    
#mouseclick event
mapcanvas.bind("<Button 1>",printcoords)






modeframe = Canvas(CW,width=mapx, height=Wsy-mapy)
modeframe.place(x=0, y=mapy)
New_line=Button(modeframe,text="New line", command = New_line_func)
Delete_line=Button(modeframe,text="Delete line", command = Delete_line_func)
Calibrate_last_point=Button(modeframe,text="Calibrate last point", command = Calibrate_last_point_func)
Convert_and_save=Button(modeframe,text="Convert and save", command = Convert_and_save_func)

Delete_line.place(x=20, y=20)
New_line.place(x=85,y=20)
Calibrate_last_point.place(x=150,y=20)
Convert_and_save.place(x=300,y=20)




CW.mainloop()


