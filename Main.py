#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 09:33:01 2019

@author: el
"""
#Packages
#not every package are necessary
import sys
import os
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import geopandas as gpd
from shapely.geometry import Point,LineString,MultiPoint,Polygon,MultiLineString,shape
import shapely
import fiona
import json
import folium
from folium.plugins import MarkerCluster
import branca.colormap as cm
import datetime
from random import randint

#Just want to see better
pd.set_option('max_columns', 7)
#%% pathes YOU WILL need to edit
#Data Path where the mediaMobildata are stored
data_path='/home/el/Data/fcd_mediamobile_2017_2018/'
#Executable Path 
X_path='/home/el/Codes/bla/Lyo-FCD/FCD/fcd-lyo/'
hehe=os.getcwd()

if(hehe==X_path):
    print('Till then, this is working ...')
else:
    os.chdir(X_path)
    
    
    
############################################################ LINKS ####################################    
# %% importing links data
links = pd.read_csv(data_path+ 'Arc/Links', sep =';')
#Converting the ',' french to '.' decimals
links['length']=links['length'].apply(lambda x:x.replace(',','.'))
links['length']=links['length'].astype(float)#FLoating it
links.head(5)
# %% Trying to plot to make sure we are dealing with links
#I'm just making a Geopandas dataframe because it can be easier to play with later on
# Here the challenge is to break the geom columns of the link

#init list
temp=[]
Px=[]
for index, row in links.iterrows():
      temp=row['geom'].split('|')
      tempx=[]
      tempy=[]
      c=[]
      for bla in temp:
            c.append([float(bla.split(',')[0]),float(bla.split(',')[1])])
      Px.append(LineString(c)) #creating a linestring, for plotting it will be smoother
      
links['geometrie']=Px #creating a new column
gdf = gpd.GeoDataFrame(links, geometry='geometrie')# creating the geopanda dataframe
gdf.crs = {'init' :'epsg:4326'}#You need to give an ellipsoid if you want to play georef.
#I deal with WG84 most of the timem but for symuvia, we will need to project on Lambert 93
#gdf.plot()#depending on you available memory this can take ages

# %% This section is used to generate a nice looking folium html web page


bo=gdf.total_bounds#I'm using my geopandas dataframe to find the bound.. a bit overkill
center=(bo[1] + bo[3])/2, (bo[0] + bo[2])/2
center=(45.74808,4.82355)#let us make it simpler

#instaciating the folium engine!
m=folium.Map(center,zoom_start=12,tiles='OpenStreetMap')

h = folium.FeatureGroup(name='Links')

#you can change your colormap, however be carefule of the perceptually uniform colormap
cmap = mpl.cm.autumn

#Here two possibilities, either you take only a certain range of your geodataframe, or you random select
nama=[]
temp=[]
locations=[]
mini=0
maxi=5000
for idx,row in gdf[mini:maxi].iterrows():
    nama=str(row['id'])
    temp=row['geom'].split('|')#Re6doing what I just did before but easier to deal zith for now
    
    locations=[]
    for bla in temp:
          locations.append([float(bla.split(',')[0]),float(bla.split(',')[1])])
    
    h.add_child(folium.PolyLine(locations,color=mpl.colors.rgb2hex(cmap(idx/float(len(gdf[mini:maxi])))),weight=2.5, opacity=1))

m.add_child(h)

m.save('links.html')
#So the colormap does not mean anything, and it gives vision biais as well, but at least it can help to
#segment

#%% It starts to be pretty funky-funky when you want to segment the data depending on a polygon
#this will be useful for cutting your data depending on certain area (how many cars in/out)

layer_file='./Shapy/Nicosoffice.shp'#let us take a shapefile (made zith QGIS) around Nicolas' office

shapi = fiona.open(layer_file).next()
shape = shapely.geometry.asShape( shapi['geometry'] )
x, y = shape.exterior.coords.xy
bloub=[]
for blix,bliy in zip(x,y):#FOr some reasno the lat and long are inversed... So I', fliping..
      bloub.append([bliy,blix])
polyg = shapely.geometry.Polygon(bloub)# and remaking the polygon   


aa=[]
gdf['InOut']=pd.Series()#I'll use that to discriminate my data which are in or out
for idx,row in gdf.iterrows():
    path=row['geometrie']
    aa.append(path.intersects(polyg))
    
print('Vrai='+str(aa.count(True))+' Faux='+str(aa.count(False))) 
gdf['InOut']=aa

#Killing the data which are out of the polygon
indexounet=gdf[gdf['InOut']==False].index
gdf.drop(indexounet, inplace=True)


#%% Making the cutted map

center=(45.74808,4.82355)

m=folium.Map(center,zoom_start=12,tiles='OpenStreetMap')
locations=[]
popups=[]
nama=[]

h = folium.FeatureGroup(name='LinksCut')


cmap = mpl.cm.autumn
milou=gdf['InOut'].max()#normalisation
for idx,row in gdf.iterrows():
    nama=str(row['id'])
    temp=row['geom'].split('|')
    
    locations=[]
    for bla in temp:
          locations.append([float(bla.split(',')[0]),float(bla.split(',')[1])])
    
    h.add_child(folium.PolyLine(locations,color=mpl.colors.rgb2hex(cmap(row['InOut']/milou)),weight=2.5, opacity=1))
    #popups.append(nama)

m.add_child(h)

m.save('links-cut.html')
#you have a map cutm pretty useful for all the other analysis




###############################################Position###########################################
#%% Let us now focus on Position data I did not play that much with it....
# reading the data, once again think about the correctness of your pathes
One_day_positions = pd.read_csv(data_path+ 'Positions/201710/Positions_20171001.csv', sep =';', header = -1, names = ["vehicleID", "timestamp", "latitude", "longitude"] )
One_day_positions.head(5)
#%%
One_day_positions['Coordinates'] = list(zip(One_day_positions.latitude, One_day_positions.longitude))
One_day_positions['Coordinates'] = One_day_positions['Coordinates'].apply(Point)
#gdf = gpd.GeoDataFrame(One_day_positions, geometry='Coordinates')
#gdf.plot()
number_of_Vehicule=len(set(list(One_day_positions.vehicleID)))
# %%
One_day_positions['timestamp'] = pd.to_datetime(One_day_positions['timestamp'])
veh_trip = One_day_positions.groupby('vehicleID').agg({'timestamp': ['min', 'max', 'count']})
veh_trip.columns = list(map(''.join, veh_trip.columns.values))
veh_trip['trip_duration'] = (veh_trip['timestampmax'] - veh_trip['timestampmin']).dt.total_seconds()
veh_trip['frequence'] = (veh_trip['trip_duration'] / veh_trip['timestampcount']).round()
veh_trip.head(5)


# %%
Veh=One_day_positions[One_day_positions['vehicleID']==One_day_positions['vehicleID'][0]]
gdf = gpd.GeoDataFrame(Veh,geometry='Coordinates')
gdf.crs = {'init' :'epsg:4326'}
gdf.plot()

################################################################ Observations ####################
# %% My Aim here in this full section is to link Observations (Each of them have a speed and a linkID) to VehicleID
# and then to positionning

#%% First we need to get the obsevation
One_day_observations = pd.read_csv(data_path+ 'Observations/201710/Observations_20171001.csv', sep =';', header = 0)
#This might be useful for later, if we want to play with time
#One_day_observations['timestamp']=pd.to_datetime(One_day_observations['timestamp'])
One_day_observations.head(10)


# %% Then I want to get the Vehicule ID attached to link
One_day_tracks = pd.read_csv(data_path+'Tracks/201710/Tracks_20171001.csv', sep =';')
One_day_tracks.head(5)


PPx=[]
Px=[]
Veh=[]
for index, row in One_day_tracks.iterrows(): #It can take 45-60 secondes to run, dont worry
      PPx=[]
      PPx.append(str(row['obsIdList']).split('|')) #Same trick as before
      for i,v in enumerate(PPx):
            second=v
            if('nan' in second):
                  second[second.index('nan')]=-999
                  
            for j,w in enumerate(second):
                  Px.append(np.int(w))
                  Veh.append(row['vehicleId'])
     
# %% I'm construction a dataframe where I have the observqtion ID associated to the vehicule ID,
# I simply exploded the trakcs by observation ID, saying differently                  

Veh_and_lks=pd.DataFrame({'id':Px,'Vehicle ID':Veh}) #Each observation is associated to a Veh
Veh_and_lks.head(5)

#%% SO know I want to make a big Datframe where I match The observation ID to LinkID
Vehicule_and_tracks=pd.merge(Veh_and_lks, One_day_observations, on='id').fillna(0)
#The fillna(0) can be crucial here depending on the way you want to treat the absence of data for merging
Vehicule_and_tracks.head(20)
#So now we have, ObsId,VehicleID,LinkID,Time qnd Speed in one neat dataframe

# %%Next step is adding the geopositionning of the dataframe

B=links.loc[:,['id','geom','length']]# I'm selecting only some column here from the link
B.rename(columns={'id':'linkId'},inplace=True)#Watcha, here the ID is the ID of the link!, but my bigdataframe is the ID of the observation
total=pd.merge(Vehicule_and_tracks,B, on='linkId').fillna(0)# I merge... Same remark on the fillna!
total.head(20)
# %% So, I've a bigdataframe with everything I needed to plot a map of speed.

#centering my map, I'm not fancy anymore here
center=(45.74808,4.82355)
#init of the foliu; object
m=folium.Map(center,zoom_start=12,tiles='OpenStreetMap')
locations=[]
popups=[]
nama=[]

h = folium.FeatureGroup(name='Speedy')

#I'm going to plot only vehicule, here, so I'll goup by
grouped=total.groupby('Vehicle ID')
##It is useful to look if it actually did grouped
groups = dict(list(grouped))

#This is a branca colormap here,
colormap=cm.linear.RdYlGn_09.scale(0,100)
colormap.caption = 'Speed Km/H'
mamax=100#I'm scaling my colormap to 100 km/h because I cannot take the maxm since I'm not taking all the VEH

# Here I'll select vehicles randomly
kekeys=list(grouped.groups.keys())
generandom=[randint(0, len(kekeys)) for p in range(200) ]#I'm selecting 200 hundereds vehicles

for glip in generandom:#looping over my random selection,will take about a min for 200 vehs
      group=grouped.get_group(kekeys[glip])# I'm selecting my vehicle
      nama=group['Vehicle ID'].values[0]#I'm getting the name of my vehicule

      for bla,row in group.iterrows():#now I'm looping over my vehicle data (speed and link)
          locations=[]

          temp=row['geom'].split('|')#Spliting the linestring of geometry 
          for bla in temp:
                      locations.append([float(bla.split(',')[0]),float(bla.split(',')[1])]) #appending the location on my map
          h.add_child(folium.PolyLine(locations,popup=nama,tooltip=nama,color=mpl.colors.rgb2hex(colormap(row['speedInKph'])),weight=7, opacity=1))
          #The former lines is setting my color depending on the speed and setting the label when the mouse pass by


m.add_child(h)

m.add_child(colormap)
m.save('Vehicule.html')
#Remarks, you have to keep in mind, that if you have two veh which take the same path or part of the same part
#what you will see in the map will be the last traces you plotted, so there is NO time statistics on what you see in the map
#It is only visualisation



# %%%%%% Now that we have a vehicule list with speed and length of the link we can generate a pseudo 
# temps de parcours distribution, the thing is, they are over estimated here but it gives a first raw sense
# that we are actually playing with the correct numbers

grouped=total.groupby('Vehicle ID')

tps_parcours=[]
geo_O=[]
geo_D=[]
timi=[]
for name, group in grouped:
      bla=group['length']/(group['speedInKph']*1000/60)
      bla.replace([np.inf,-np.inf], np.nan,inplace=True)
      tps_parcours.append(bla.sum())
      geo_O.append(group['geom'].values[0].split('|')[0].split(','))#I'm saving the position for the next section
      geo_D.append(group['geom'].values[-1].split('|')[0].split(','))

      #group['timestamp'].plot()
      #input('crap')

#plt.plot(group.index,group['id'].sort_values())
#plt.show()
f1,ax1=plt.subplots(1,1,figsize=(25,25))
ax1.grid(color='k', linestyle='-', linewidth=2)
ax1.hist(tps_parcours,bins=np.arange(0,100,1),color='red',density=True)
ax1.set_xlabel('minutes')
ax1.set_ylabel('Density')
f1.savefig('tempsParcours.png',dpi=200)


# %%And then If I have temps de parcours and position I can make a map of it

import branca.colormap as cm
center=(45.74808,4.82355)

m=folium.Map(center,zoom_start=12,tiles='OpenStreetMap')
locations=[]
popups=[]
nama=[]

h = folium.FeatureGroup(name='Temps de parcours')

mini=0
maxi=50


colormap=cm.linear.RdYlGn_09.scale(np.min(tps_parcours[mini:maxi]),np.max(tps_parcours[mini:maxi]))
colormap = cm.LinearColormap(colors=['green','red'], vmin=np.min(tps_parcours[mini:maxi]),vmax=np.max(tps_parcours[mini:maxi]))
colormap.caption = 'temps de Parcours [min]'

locations=[]
popups=[]
totools=[]
for TPS,GeO,GeD in zip(tps_parcours[mini:maxi],geo_O[mini:maxi],geo_D[mini:maxi]):
       
       
       h.add_child(folium.Marker(location=[float(GeO[0]),float(GeO[1])],popup=str(TPS),icon=folium.Icon(color='white',icon_color=mpl.colors.rgb2hex(colormap(TPS)))))
       h.add_child(folium.Marker(location=[float(GeD[0]),float(GeD[1])],popup=str(TPS),icon=folium.Icon(color='white',icon_color=mpl.colors.rgb2hex(colormap(TPS)))))
       #you can use the next line If you want to See the OD couples
       #h.add_child(folium.PolyLine([[float(GeO[0]),float(GeO[1])],[float(GeD[0]),float(GeD[1])]],color=mpl.colors.rgb2hex(colormap(TPS)),weight=7, opacity=1))

   

m.add_child(h)
m.add_child(colormap)
m.save('TpsParcrs.html')
#this map does not make so much sense but it can be upgraded easily


# %% This section gives you a way to see the OD concentrationm thios is actually the same map as before
# but with an other way to see it

from folium.plugins import HeatMap
import branca.colormap as cm
center=(45.74808,4.82355)

m=folium.Map(center,zoom_start=12,tiles='OpenStreetMap')
locations=[]
popups=[]
nama=[]
mini=0
maxi=5000
colormap=cm.linear.RdYlGn_09.scale(np.min(tps_parcours[mini:maxi]),np.max(tps_parcours[mini:maxi]))
colormap = cm.LinearColormap(colors=['green','red'], vmin=np.min(tps_parcours[mini:maxi]),vmax=np.max(tps_parcours[mini:maxi]))
colormap.caption = 'temps de Parcours [min]'

h = folium.FeatureGroup(name='Temps de parcours')

locations=[]
maxima=np.max(tps_parcours[mini:maxi])

for TPS,GeO,GeD in zip(tps_parcours[mini:maxi],geo_O[mini:maxi],geo_D[mini:maxi]):
      locations.append([float(GeO[0]),float(GeO[1]),TPS/maxima])
      #h.add_child(folium.Marker(location=[float(GeO[0]),float(GeO[1])],popup=str(TPS),icon=folium.Icon(color='white',icon_color=mpl.colors.rgb2hex(colormap(TPS)))))
      #h.add_child(folium.Marker(location=[float(GeD[0]),float(GeD[1])],popup=str(TPS),icon=folium.Icon(color='white',icon_color=mpl.colors.rgb2hex(colormap(TPS)))))




HeatMap(locations).add_to(m)
m.add_child(h)
m.save('heat.html')



############################################### Speed data ##########################
#%% This section will focus on the speed data
# depending on your memory I would suggest to start zith only 100 lines :D
One_day_speeds = pd.read_csv(data_path+'Speeds/201710/Speedavg_20171001.csv', sep =';',nrows=100)

One_day_speeds=One_day_speeds.set_index('linkId') #It is easier to drop the index and play zith linkid
One_day_speeds.replace(0, np.nan, inplace=True)#killing weros for stats
nama=list(range(0,480))#I'm renaming the columns for simplicity
One_day_speeds.columns=nama
#%% Remerber the links has geometrical info
B=links.loc[:,['id','geom','length']]
B.rename(columns={'id':'linkId'},inplace=True)
Speed_and_Geom=pd.merge(One_day_speeds,B, on='linkId').fillna(0)
Speed_and_Geom.head(20)
#So now I have speed every three minutes geolocalized!

#%% To change a bit I'm trying to develop in the following line a heatmap timed
from folium.plugins import HeatMap,HeatMapWithTime
import branca.colormap as cm
center=(45.74808,4.82355)

m=folium.Map(center,zoom_start=12,tiles='OpenStreetMap')

h = folium.FeatureGroup(name='Temps de parcours')

locations=[]


mamax=100#scaling my speed here
dimi=[]
for pp in np.arange(1,480,1):
      locations=[]
      for idx,row in Speed_and_Geom.iterrows():
            temp=row['geom'].split('|')
            for bla in temp:
                  locations.append([float(bla.split(',')[0]),float(bla.split(',')[1]),row[pp]/mamax])
                  
      dimi.append(locations)
    

    



HeatMapWithTime(dimi,radius=20,gradient={0: 'green', 1: 'red'}).add_to(m)
m.add_child(h)
m.save('Timedheat.html')
#this map does not bring much with its current version, but I guess there might have potential on the next upgrade


