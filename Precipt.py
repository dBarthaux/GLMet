# -*- coding: utf-8 -*-
"""
Created on Sun Dec 22 20:16:41 2024

@author: dundu
"""

from datetime import datetime, timedelta
import urllib
import numpy as np
# import pandas as pd
import glob
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

# =============================================================================
# 
# =============================================================================

Today = datetime.today().strftime('%Y-%m-%d')
TodayAlt = Today.replace('-', '')

Date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
Date2 = Date.replace('-', '')

URL = f'https://dd.weather.gc.ca/{Date2}/WXO-DD/model_hrdps/continental/2.5km/18/'

Filenames = '*HRDPS_PRATE*.grib2'

fxxs = np.arange(12, 36)

for x in fxxs:
    
    # Define the string of the model step
    strfxstep = str(x)
    if len(strfxstep) == 1:
        fxstep = f'00{strfxstep}'
    if len(strfxstep) == 2:
        fxstep = f'0{strfxstep}'
    if len(strfxstep) == 3:
        fxstep = strfxstep
    
    PRate = f'{Date2}T18Z_MSC_HRDPS_PRATE_Sfc_RLatLon0.0225_PT{fxstep}H.grib2'
    
    # Download all the grib files
    urllib.request.urlretrieve(URL+fxstep+'/'+PRate, 'Temporary/'+PRate)

    print(r'Downloading HRDPS Hour {0}'.format(x), end='\r')


print('Loading HRDPS files...')
# Lists of all the filenames by variable
PFiles = glob.glob(f"Temporary/{Filenames}")

# Load the dataset
dsP = xr.open_mfdataset(PFiles, engine='cfgrib', 
                         combine='nested', concat_dim='step')

Lats = dsP.latitude.values
Lons = dsP.longitude.values
Pras = dsP.prate.values*86400 # Convert
Pras[Pras == 0] = np.nan

Test = Lats[(Lats >= 40) & (Lats <= 50)]

scale = '50m'

# KColors = pl.cm.jet(np.linspace(0, 1, Hours.size))

# Province borders, from sienna22 on stack exchange
states_provinces = cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_1_states_provinces_lines', scale='50m', facecolor='none')


Fig = plt.figure(figsize=(7,7))
ax = plt.axes(projection=ccrs.PlateCarree())
for x in range(Pras.shape[0]):
    ax.set_title(str(dsP.valid_time.values[x]).split('T')[1][:5])
    ax.set_extent([-80, -70, 40, 50])
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(states_provinces, edgecolor='black', linestyle='dashed')
    
    rain = ax.contourf(Lons, Lats, Pras[x], cmap='Blues',
                       vmin=0, vmax=np.nanmax(Pras))
    
    ax.add_feature(cfeature.LAKES, edgecolor='k', linewidth=0.3)
    
    ax.scatter(-73.579185, 45.504926, marker='*', edgecolor='k', 
               facecolor='red', s=200, zorder=10)
    
    # cbar = Fig.colorbar(rain, ax=ax, orientation='horizontal',
    #                       fraction=0.1, pad=0.05, shrink=0.75)
    # cbar.set_label('Precipitation Rate [mm/day]',
    #                 fontsize=12)

    # plt.tight_layout()
    plt.pause(2)
    plt.cla()





