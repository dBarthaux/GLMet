# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 10:38:58 2024

@author: dundu
"""

import loadfuncs as fx
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from windrose import WindroseAxes, plot_windrose
# from urllib import request
# # import json
# from bs4 import BeautifulSoup
# import re
# import xmltodict
import pickle
# import xarray as xr
# from herbie import Herbie
# import urllib.request
# import os
# import glob

# =============================================================================
# 
# =============================================================================

# List of extra dependencies:
# Herbie
# windrose
# beautifulsoup
# xmltodict
# cfgrib

# To do:
# x) What the fuck is wrong with this precipitation data?

# MCTAVISH	71612	7024745	45.504926	-73.579185	72.583 CWTA

# When the code runs, it does three things:
# Models: First checks if a file has already been made. If yes, load it.
#         If no, run the function that downloads the model data.

# Observ: Updates the observations for that day (if no observations, creates
#         the file).

# Plotts: Creates the plots and saves the PNGs.

# If Sunday, delete all data (no reason to keep)

# Station information
Latitude = 45.504926
Longitude = -73.579185
Code = 'CWTA'
Name = 'McTavish'
UTC = 5

Today = datetime.today().strftime('%Y-%m-%d')
Today2 = Today.replace('-', '')
Yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

# List of US models and cycle times to load
USModels = ['hrrr 18', 'gfs 18', 'gefs 18', 'nam 18', 'nbm 12', 'ecmwf 12']

# Get station data
ObsData = fx.ECStationData(Code)
# Convert data type
ObsData.iloc[:,:4] = ObsData.iloc[:,:4].astype(float)

# Get Canadian data
try:
    # Check if file already made
    File = open(f'Data/EC_ModelData/ECMods_{Code}_{Today2}.pickle', 'rb')
    # Dump information
    ECData = pickle.load(File)
    # close the file
    File.close()
except:
    # If not, load 'em up
    ECData = fx.CanadianModels(Latitude, Longitude, Code)
    
# Get American/Other data
try:
    # Check if file already made
    File = open(f'Data/US_ModelData/USMods_{Code}_{Today2}.pickle', 'rb')
    # Dump information
    USData = pickle.load(File)
    # close the file
    File.close()
except:
    # If not, fire up the ol' Herb-a-derb
    USData = fx.ModelOutput(USModels, Yesterday, Latitude, 
                            Longitude, Code, units=1)


# Convert time from UTC to Montreal Local
ObsData.index = pd.to_datetime(ObsData.index)
ObsData.index = ObsData.index - pd.to_timedelta(5, unit='h')
for m in ECData.keys():
    ECData[m].index = pd.to_datetime(ECData[m].index)
    ECData[m].index = ECData[m].index - pd.to_timedelta(5, unit='h')
for m in USData.keys():
    if USData[m].shape[0] > 0:
        USData[m].index = USData[m].index - pd.to_timedelta(5, unit='h')


# For formatting date with matplotlib
myFmt1 = mdates.DateFormatter('%d %H')

Fig1 = plt.figure(figsize=(14,8))
Fig1.suptitle(f'Temperature at {Name}, {Today}\n Models Initialized Yesterday at 18Z or 12Z', fontsize=15)
ax1 = Fig1.subplots()
ax1.plot(ObsData['Temperature [C]'], label='Obs', c='k', linewidth=2)

for m in ECData.keys():
    ax1.plot(ECData[m]['Temperature [C]'], label=m.upper(), linewidth=1.5)

for m in USModels:
    if USData[m.split()[0]].size != 0:
        ax1.plot(USData[m.split()[0]]['Temperature [C]'], 
                 label=m.split()[0].upper(), linewidth=1.5)

ax1.xaxis.set_major_formatter(myFmt1)

ax1.legend(prop={'size':15}, ncols=2)
ax1.set_xlabel('Time [Local, DD HH]', fontsize=15)
ax1.set_ylabel('Temperature [C]', fontsize=15)
plt.tight_layout()
plt.savefig(f'Figures/Temperature_{Code}_{Today2}.png')
plt.close()


Fig2 = plt.figure(figsize=(14,8))
Fig2.suptitle(f'Wind at {Name}, {Today}\n Models Initialized Yesterday at 18Z or 12Z', fontsize=15)
ax21 = plt.subplot(121)
ax22 = plt.subplot(122, projection='windrose')

ax21.set_title('Speed', fontsize=14)
ax22.set_title('Obs. Direction', fontsize=14)

ax21.plot(ObsData['Wind Speed [m/s]'].rolling(50).mean(), 
         label='Obs (Rolling Mean)', c='k', linewidth=2)

for m in ECData.keys():
    ax21.plot(ECData[m]['Wind Speed [m/s]'], label=m.upper(), linewidth=1.5)

for m in USModels:
    if USData[m.split()[0]].size != 0:
        ax21.plot(USData[m.split()[0]]['Wind Speed [m/s]'], 
                 label=m.split()[0].upper(), linewidth=1.5)

ax21.xaxis.set_major_formatter(myFmt1)

ax21.legend(prop={'size':11}, ncols=3)
ax21.set_xlabel('Time [Local, DD HH]', fontsize=15)
ax21.set_ylabel('Wind Speed [m/s]', fontsize=15)

ForRose = ObsData[['Wind Direction [deg]', 'Wind Speed [m/s]']].copy()
ForRose.columns = ['direction', 'speed']
ForRose = ForRose.astype(float)

ax22.bar(ForRose['direction'], ForRose['speed'],
        normed=True, opening=0.8, edgecolor="white")

ax22.legend()

plt.tight_layout()
plt.savefig(f'Figures/Wind_{Code}_{Today2}.png')
plt.close()


# # Clean precipitation data before plotting
# ObsData['Precipitation [mm]'][ObsData['Precipitation [mm]'] < 0] = 0

# Fig3 = plt.figure(figsize=(14,8))
# Fig3.suptitle(f'Precipitation at {Name}, {Today}\n Models Initialized Yesterday at 18Z or 12Z', fontsize=15)
# ax3 = Fig3.subplots()

# ax3.plot(ObsData['Precipitation [mm]'], label='Obs', c='k', linewidth=2)

# for m in ECData.keys():
#     ax3.plot(ECData[m]['Precipitation [mm]'], label=m.upper(), linewidth=1.5)

# for m in USModels:
#     if USData[m.split()[0]].size != 0:
#         ax3.plot(USData[m.split()[0]]['Precipitation [mm]'], 
#                  label=m.split()[0].upper(), linewidth=1.5)

# ax3.xaxis.set_major_formatter(myFmt1)
# ax3.legend(prop={'size':15}, ncols=2)
# ax3.set_xlabel('Time [Local, DD HH]', fontsize=15)
# ax3.set_ylabel('Precipitation [mm]', fontsize=15)
# plt.tight_layout()