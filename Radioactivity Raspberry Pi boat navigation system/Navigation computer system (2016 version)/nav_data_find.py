#Functions for gathering and processing navigational data


#Main function for getting all the navigational data and returning it in list form
def nav_data_grab():
    global Mag_dec
    nav_data_list=[0]*20
    nav_data_list[0]=['Magnetic Bearing', round(compass.get_currentValue(),0)]
    nav_data_list[1]=['Magnetic Declination', Mag_dec]
    nav_data_list[2]=['GPS track', round(gpsd.fix.track)]
    nav_data_list[3]=['GPS speed kph', round(gpsd.fix.speed,2)]
    nav_data_list[4]=['GPS lat decimal', gpsd.fix.latitude]
    nav_data_list[5]=['GPS long decimal', gpsd.fix.longitude]
    nav_data_list[6]=['GPS time', gpsd.fix.time]
    nav_data_list[7]=['Roll value degrees', roll.get_currentValue()]      
    nav_data_list[8]=['Pitch value degrees', pitch.get_currentValue()]         
    nav_data_list[9]=['Lateral acceleration g', accelerometer.get_xValue()]
    nav_data_list[10]=['Longitudinal acceleration g', accelerometer.get_yValue()]
    nav_data_list[11]=['Vertical acceleration g', accelerometer.get_zValue()]
    return nav_data_list

#Process navigation data for display purposes
def nav_data_process(basic_nav_data,MTC,simmode, simtable,simcount):
    nav_process_list=[0]*20
    Disp_bearing=0
    Disp_speed=round(basic_nav_data[3][1]*1.94384,2)
    if MTC.get() ==1:
        Disp_bearing=basic_nav_data[0][1]
    if MTC.get() ==2:
        Disp_bearing=basic_nav_data[0][1]+basic_nav_data[1][1]
    if MTC.get()==3:
        Disp_bearing=basic_nav_data[2][1]

    #Handle simulation needs
    if simmode[0]==1:
        if MTC.get()==3:
            Disp_bearing=round(simtable[simcount]*180+180)
    if simmode[2]==1:
        if MTC.get()<3:
            Disp_bearing=round(simtable[simcount]*180+180)
    if simmode[1]==1:
        Disp_speed=round(simtable[simcount]*5+5,2)    
    
    #Add trailing zeroes to bearing section    
    Cbt=StringVar()
    Cbt.set('')
    if Disp_bearing<100:
        if Disp_bearing<10:
            Cbt.set('00%d' % (Disp_bearing))
        if Disp_bearing>9:
            Cbt.set('0%d' % (Disp_bearing))
    else:
        Cbt.set('%d' % (Disp_bearing))
    
    nav_process_list[0]=['Display bearing value',Disp_bearing]
    nav_process_list[1]=['Display bearing text',Cbt]
    nav_process_list[2]=['GPS track',basic_nav_data[2][1]]
    nav_process_list[3]=['GPS speed in knots',Disp_speed]
    nav_process_list[4]=['Latitude in DMS',dmsmodule.decdeg2dms(basic_nav_data[4][1],'lat')]
    nav_process_list[5]=['Longitude in DMS',dmsmodule.decdeg2dms(basic_nav_data[5][1],'long')]
    nav_process_list[6]=['GPS time', gpsd.fix.time]
    nav_process_list[7]=['Roll value degrees', round(basic_nav_data[7][1])]      
    nav_process_list[8]=['Pitch value degrees', round(basic_nav_data[8][1])]         
    nav_process_list[9]=['Lateral acceleration m/s', round(basic_nav_data[9][1]*9.81,3)]
    nav_process_list[10]=['Longitudinal acceleration m/s', round(basic_nav_data[10][1]*9.81,3)]
    nav_process_list[11]=['Vertical acceleration m/s', round(basic_nav_data[11][1]*9.81,3)]
    
    return nav_process_list
