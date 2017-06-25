# -*- coding: utf-8 -*-
#Various useful functions for navication
# decdeg2dms converts decimal degrees to Degrees, Minutes and Seconds
# nav_data_process formats data in a list for navigational purposes
# calculate_initial_compass_bearing calculates the bearing between two decimal lat and long points

import math
import csv

def decdeg2dms(dd,latlong):
    if math.isnan(dd) ==False: ##This simple check was added because my paticular GPS unit had a habbit of sticking in NaNs

        negative = dd < 0
        dd = abs(dd)
        minutes,seconds = divmod(dd*3600,60)
        degrees,minutes = divmod(minutes,60)
        if negative:
            if degrees > 0:
                degrees = -degrees
            elif minutes > 0:
                minutes = -minutes
            else:
                seconds = -seconds

        #Round out
        degreesr=abs(int(round(degrees)))
        minutesr=int(round(minutes))
        secondsr=round(seconds,4)

        #Decide N,S,E or W
        des=''
        if latlong=="lat":
            if degrees<0:
                des="S"
            if degrees>0:
                des="N"
        if latlong=="long":
            if degrees<0:
                des="W"
            if degrees>0:
                des="E"

        DMS=''
        DMS=str(degreesr)+'D '+str(minutesr)+"M "+str(secondsr)+'"'+des

    else:
        DMS='Math error'
        print dd
    return DMS

#Process navigation data for display purposes
def nav_data_process(basic_nav_data,MTC,simmode, simtable,simcount,Cbt,Spd,Vad,sim_course_data,nowtime):

    nav_process_list=[0]*20
    Disp_bearing=0
    Raw_speed=(basic_nav_data[4][1]*1.94384)
    Disp_speed=round(Raw_speed,2)
    
    
    if MTC.get() ==1:
        Disp_bearing=basic_nav_data[1][1]+basic_nav_data[0][1]
        lm=1
    if MTC.get() ==2:
        lm=2
        Disp_bearing=basic_nav_data[1][1]+basic_nav_data[2][1]+basic_nav_data[0][1]
    if MTC.get()==3:
        lm=2
        Disp_bearing=basic_nav_data[3][1]

    #Handle simulation needs
    if simmode[0]==1:
        if MTC.get()==3:
            Disp_bearing=round(simtable[simcount]*180+180)
    if simmode[2]==1:
        if MTC.get()<3:
            Disp_bearing=round(simtable[simcount]*180+180)
    if simmode[1]==1:
        Disp_speed=round(simtable[simcount]*5+5,2)
    if simmode[3]==0:
        declat=basic_nav_data[5][1]
        declong=basic_nav_data[6][1]
        rangenext=basic_nav_data[17][1]
        bearingnext=basic_nav_data[18][1]
    if simmode[3]==1:
        timeelapsed=(nowtime-sim_course_data[4])/3600
        simbearing=sim_course_data[2]
        simspeed=sim_course_data[3]
        simdis=timeelapsed*simspeed
        simstartlat=sim_course_data[0]
        simstartlong=sim_course_data[1]
        ll2=lat_long_from_range_bearing(simstartlat,simstartlong,simdis,simbearing,'nm')
        declat=ll2[0]
        declong=ll2[1]

        waylat=basic_nav_data[15][1]
        waylong=basic_nav_data[16][1]
        rangenext=range_sphere(declat,declong,waylat,waylong,'nm')
        bearingnext=calculate_initial_compass_bearing(declat,declong,waylat,waylong)

        
    #Add trailing zeroes to bearing section    

    Cbt.set('')
    if Disp_bearing<100:
        if Disp_bearing<10:
            Cbt.set('00%d' % (Disp_bearing))
        if Disp_bearing>9:
            Cbt.set('0%d' % (Disp_bearing))
    else:
        Cbt.set('%d' % (Disp_bearing))

    #Format speed setting
    Spd.set(str(round(Disp_speed,1)))

    #Correct longitudinal acceleration for pitch value
    uncor_long_acc=basic_nav_data[10][1]*9.81
    pitch_deg=basic_nav_data[9][1]
    cor_long_acc=remove_heal_from_accleration(uncor_long_acc,pitch_deg)
 
    #Format vario setting
    vario=round(cor_long_acc,1)
    if vario>0:
        Vad.set('+'+str(vario))
    else:
        Vad.set(str(vario))   

   

    #Time extraction
    full_time=str(basic_nav_data[7][1])
    curr_time=full_time[11:-5]
    
    nav_process_list[0]=['Display bearing value',Disp_bearing]
    nav_process_list[1]=['Display bearing text',Cbt]
    nav_process_list[3]=['GPS track',basic_nav_data[3][1]]
    nav_process_list[4]=['GPS speed in knots',Disp_speed]
    nav_process_list[5]=['Latitude in DMS',decdeg2dms(declat,'lat')]
    nav_process_list[6]=['Longitude in DMS',decdeg2dms(declong,'long')]
    nav_process_list[7]=['GPS time',curr_time ]
    nav_process_list[8]=['Roll value degrees', round(basic_nav_data[8][1])]      
    nav_process_list[9]=['Pitch value degrees', pitch_deg]         
    nav_process_list[10]=['Longitudinal acceleration m/s', cor_long_acc]
    nav_process_list[11]=['Lateral acceleration m/s', round(basic_nav_data[11][1]*9.81,3)]
    nav_process_list[12]=['Vertical acceleration m/s', round(basic_nav_data[12][1]*9.81,3)]
    nav_process_list[13]=['Range to next waypoint', str(round(rangenext,2))]

    if lm==2:
        bearing=str(round(bearingnext))
        bearingtext=' D True'
    if lm==1:
        bearing=str(round(bearingnext-basic_nav_data[2][1]))
        bearingtext=' D Mag'
    nav_process_list[14]=['Bearing to next waypoint',bearing]     
    nav_process_list[15]=['Type of bearing to next waypoint',bearingtext]
    nav_process_list[16]=['Decimal lat',declat]
    nav_process_list[17]=['Decimal long',declong]
  
    return nav_process_list



### Function for removing gravity from the lateral or longitudinal acceleration
def remove_heal_from_accleration(uncor_acc,lean_deg):
    radia=math.radians(lean_deg)
    cor_acc=uncor_acc-9.81*math.sin(radia)
    return cor_acc


#Function for setting up the axis of a chart to accuratly display lat and long
def location_axis(cenlat,cenlong,chxsize,chysize,lat_scale):

    #Find Y1 and Y2. 0.01666667 degrees latitude= 1nm = Fairly constant
    y1=cenlat-(lat_scale/2)*0.01666667
    y2=cenlat+(lat_scale/2)*0.01666667

    long_scale=lat_scale*(chxsize*1.1)/(chysize*1.1) # Number of NM across horosontal axis

    #number of degrees longitude for 1nm at this latitude
    long_nm=1/(range_sphere(cenlat, 0, cenlat, 1,'nm'))
        
    x1=cenlong-(long_scale/2)*long_nm
    x2=cenlong+(long_scale/2)*long_nm
        
    lo_cation_scale=[x1,x2,y1,y2]

    return lo_cation_scale


#Function to return a group of coordinates that, when plotted, will form a box around the current position
def plot_marker(declat,declong,marker_size,lo_cation_scale,markertype,heading,roll):


    #Basic points for cross hairs marker
    if markertype==1:

        xpoints=[0]*10
        ypoints=[0]*10

        xpoints[0]=-1
        ypoints[0]=1
    
        xpoints[1]=-1
        ypoints[1]=-1

        xpoints[2]=1
        ypoints[2]=-1

        xpoints[3]=1
        ypoints[3]=1

        xpoints[4]=-1
        ypoints[4]=1
 
        xpoints[5]=1
        ypoints[5]=-1

        xpoints[6]=-1
        ypoints[6]=-1

        xpoints[7]=1
        ypoints[7]=1

        xpoints[8]=0
        ypoints[8]=1

        xpoints[9]=0
        ypoints[9]=-2

    #Boat type marker
    if markertype==2:
        tack1=-1
        tack2=1
        if roll<0:
            tack1=1
        if roll>0:
            tack2=-1

        xpoints=[0]*10
        ypoints=[0]*10

        xpoints[0]=0
        ypoints[0]=-2
    
        xpoints[1]=-.5
        ypoints[1]=0

        xpoints[2]=-.5
        ypoints[2]=2

        xpoints[3]=.5
        ypoints[3]=2

        xpoints[4]=.5
        ypoints[4]=0
 
        xpoints[5]=0
        ypoints[5]=-2

        xpoints[6]=tack1
        ypoints[6]=-1

        xpoints[7]=0
        ypoints[7]=-2

        xpoints[8]=0
        ypoints[8]=0

        xpoints[9]=tack2
        ypoints[9]=1

    #Rotate marker to heading value
    for i in range (0,len(xpoints)):
        theta=math.radians(180-heading)
        xs=xpoints[i]
        ys=ypoints[i]
        xpoints[i]=xs*math.cos(theta)-ys*math.sin(theta)
        ypoints[i]=ys*math.cos(theta)+xs*math.sin(theta)


    #Calibrate basic points for chart scale
    yoffset=(lo_cation_scale*marker_size)*(.5*.01666667)
    xoffset=(lo_cation_scale*marker_size)*(.5/(range_sphere(declat, 0, declat, 1,'nm')))

    for i in range(0,len(xpoints)):
        xpoints[i]=declong+(xpoints[i]*xoffset)
        ypoints[i]=declat+(ypoints[i]*yoffset)
  


    marker_points=[ypoints,xpoints]
    return marker_points
    


def lat_long_from_range_bearing(lat1,long1,rrange,bearing,units):

    #Multiply angle in radians by radius of earth in given units to get distance
    if units=='km':
        radius_of_earth=6371
    if units=='nm':
        radius_of_earth=3440.065
    if units=='m':
        radius_of_earth=6371000

    lat1r = math.radians(lat1) #Current lat point converted to radians
    long1r = math.radians(long1) #Current long point converted to radians
    bearingr=math.radians(bearing)  #Current bearing converted to radians

    lat2r = math.asin( math.sin(lat1r)*math.cos(rrange/radius_of_earth) + math.cos(lat1r)*math.sin(rrange/radius_of_earth)*math.cos(bearingr))

    long2r = long1r + math.atan2(math.sin(bearingr)*math.sin(rrange/radius_of_earth)*math.cos(lat1),
             math.cos(rrange/radius_of_earth)-math.sin(lat1r)*math.sin(lat2r))

    lat2 = math.degrees(lat2r)
    long2 = math.degrees(long2r)

    return [lat2,long2]


def calculate_initial_compass_bearing(lat1, long1, lat2, long2):
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    """

    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0
              
    lat1 = lat1*degrees_to_radians
    lat2 = lat2*degrees_to_radians

    diffLong = (long2-long1)*degrees_to_radians
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = round((initial_bearing + 360) % 360,0)
    return compass_bearing

#Calculate range between any two decimal degrees
def range_sphere(lat1, long1, lat2, long2,units):
    
    #Check that the two coordinates are not the same and are not the origin
    #In testing this can happen, even to 7 decimal places
    #Which, if not checked, results in a crash.

    if lat1!=lat2 or long1!=long2:
       
    
        # Convert latitude and longitude to 
        # spherical coordinates in radians.
        degrees_to_radians = math.pi/180.0
             
        # phi = 90 - latitude
        phi1 = (90.0 - lat1)*degrees_to_radians
        phi2 = (90.0 - lat2)*degrees_to_radians
             
        # theta = longitude
        theta1 = long1*degrees_to_radians
        theta2 = long2*degrees_to_radians
             
        # Compute spherical distance from spherical coordinates.
             
        # For two locations in spherical coordinates 
        # (1, theta, phi) and (1, theta', phi')
        # cosine( arc length ) = 
        #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
        # distance = rho * arc length
         
        cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
               math.cos(phi1)*math.cos(phi2))
        arc = math.acos( cos )

        #Multiply angle in radians by radius of earth in given units to get distance
        if units=='km':
            range_in_units=round(arc*6371,3)
        if units=='nm':
            range_in_units=round(arc*3440.065,3)    
        if units=='m':
            range_in_units=round(arc*6371000,3) 

    else:
        #The two GPS readings are exactly the same
        print "Zero trap deployed in Range_Sphere function"
        print "lat1, long1, lat2, long2"
        print lat1,long1,lat2,long2
        range_in_units=0.000001
   
    
    return range_in_units


#Untility for importing strings of lats and longs from a file and returning it as a list
def import_coastlines(namelats,namelongs):

    coast_lat_values=[]
    coast_long_values=[]

    with open(namelats,'rb') as csvfile:
        coast_lats_obj=csv.reader(csvfile)
        coast_lats_list=list(coast_lats_obj)


    for i in range(0,len(coast_lats_list)):
        lats_line_text=coast_lats_list[i]
        lats_line_values=map(float,lats_line_text)

        coast_lat_values.append(lats_line_values)
    
    with open(namelongs,'rb') as csvfile:
        coast_longs_obj=csv.reader(csvfile)
        coast_longs_list=list(coast_longs_obj)


    for i in range(0,len(coast_longs_list)):
        longs_line_text=coast_longs_list[i]
        longs_line_values=map(float,longs_line_text)

        coast_long_values.append(longs_line_values)

    lat_long_list=[coast_lat_values,coast_long_values]
    return lat_long_list

#Function to process the metmast data
def met_mast_correct(raw_met_data,dir_correct,spd_correct):
    processed_met_data=raw_met_data
    processed_met_data[1]=spd_correct*float(raw_met_data[1])
    processed_met_data[3]=dir_correct+float(raw_met_data[3])    

    return processed_met_data





    

        
