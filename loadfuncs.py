# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 15:00:35 2024

@author: dundu
"""

# import eccodes
from urllib import request
import shutil
import json
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from herbie import FastHerbie#, Herbie#, HerbieLatest
import xarray as xr
import xmltodict
import re
import glob
import os
import urllib.request
# import warnings
import pickle
import imageio.v2 as imageio
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
import PIL
from PIL import Image


EST = 5
EDT = 4

# =============================================================================
# 
# =============================================================================

def SundayCleaning(WholeDate):
    # If Sunday, delete all data (no reason to keep and small storage anyway)
    DayName = WholeDate.weekday() # 6 is Sunday
    DayHour = WholeDate.hour
    
    Folders = ['Figures', 'Temporary', 'Data/EC_ModelData', 'Old Figures',
               'Data/EC_StationData', 'Data/US_ModelData']
    
    if (DayName == 6) and (DayHour < 9):
        print("It's SUNDAY SUNDAY SUNDAY!")
        for fold in Folders:
            files = glob.glob(f'{fold}/*')
            for f in files:
                os.remove(f)


def MoveYesterdaysPlots(Today2):
    
    # Get the names of the files in the Figures folder
    Filenames = os.listdir('Figures')
    # Huh, I think I can just compare them as integers
    for f in Filenames:
        # Get the associated date
        Date = f[-12:-4]
        if int(Today2) > int(Date):
            shutil.move(f'Figures/{f}', 'Old Figures')

    return


def MeanTandW(ECData, USData):
    
    # Calculate model mean
    AllData = ECData | USData
    # Remove empty datasets
    Bad = []
    for d in AllData.keys():
        if AllData[d].shape[0] == 0:
            Bad.append(d)
    for b in Bad:
        AllData.pop(b)
    
    # At this point I'm sitting half on the floor - don't care if not efficient
    Tempos = []
    Winds = []
    # Get the mean temperature and wind speed
    for d in AllData.keys():
        Tempos.append(AllData[d]['Temperature [C]'])
        Winds.append(AllData[d]['Wind Speed [m/s]'])
    
    TFrame = (pd.DataFrame(Tempos).T).interpolate()
    WFrame = (pd.DataFrame(Winds).T).interpolate()
    
    TMean = TFrame.mean(axis=1)
    WMean = WFrame.mean(axis=1)
    
    return TMean, WMean


# =============================================================================
# 
# =============================================================================

def LocTime(Station):
    # Read in observation data from NWS API URL
    link = f"https://api.weather.gov/stations/{Station}/observations"
    # Read into HTML format
    html = request.urlopen(link).read()
    # Parse HTML
    soup = BeautifulSoup(html,'html.parser')
    # Convert to JSON
    site_json = json.loads(soup.text)
    # Extract the latitude and longitude of the station
    Lon, Lat = site_json['features'][0]['geometry']['coordinates']
    # Read in page that will direct us to the forecast for that location
    link = f"https://api.weather.gov/points/{Lat},{Lon}"
    # Read into HTML format
    html = request.urlopen(link).read()
    # Parse HTML
    soup = BeautifulSoup(html,'html.parser')
    # Convert to JSON
    site_json = json.loads(soup.text)
    # Get the timezone
    Timezone = site_json['properties']['timeZone']
    # Load the UTC offset dataset
    Zones = pd.read_csv('Timezones.csv')
    # Get the relevant UTC offset
    UTC = str(Zones[Zones['Name'] == Timezone]['Offset DST'].values[0])
    UTC = int(UTC.split(':')[0])
    
    return Lat, Lon, UTC


# =============================================================================
# Read in NWS Observations from the Station
# =============================================================================

def ObsData(Station):
    
    # Read in observation data from NWS API URL
    link = f"https://api.weather.gov/stations/{Station}/observations"
    # Read into HTML format
    html = request.urlopen(link).read()
    # Parse HTML
    soup = BeautifulSoup(html,'html.parser')
    # Convert to JSON
    site_json = json.loads(soup.text)
    
    # Set up measurements, not all necessary for now
    Measurements = {'Temperature [C]':[], 'Time':[], 'Precip [in]':[], 
                    'WindSpeed [km/hr]':[]}
    
    # Within "features" is a dictionary for every observation point in time
    # up until a certain timestamp. Append each.
    for i in range(len(site_json['features'])):
        Data = site_json['features'][i]['properties']
        # Switch None with NaN
        if None == Data['precipitationLastHour']['value']:
            Measurements['Precip [in]'].append(0.0)
        else:
            Measurements['Precip [in]'].append(Data['precipitationLastHour']['value'])
        Measurements['Temperature [C]'].append(Data['temperature']['value'])
        Measurements['Time'].append(pd.to_datetime(Data['timestamp']))
        Measurements['WindSpeed [km/hr]'].append(Data['windSpeed']['value'])
    
    # Convert dictionary to pandas dataframe
    ObsData = pd.DataFrame.from_dict(Measurements).set_index('Time')
    
    # Covert units where needed
    ObsData['Temp. [F]'] = (ObsData['Temperature [C]']*(9/5)) + 32
    ObsData['Wind [kts]'] = ObsData['WindSpeed [km/hr]']/1.852
    # Drop superfluous column
    ObsData = ObsData.drop(columns=['Temperature [C]', 'WindSpeed [km/hr]'])
    
    return ObsData


# =============================================================================
# Get USL Forecast Data
# =============================================================================

def USLData(Station, Today):

    # MonthNumbers = {'JAN':'01', 'FEB':'02', 'MAR':'03', 'APR':'04', 'MAY':'05',
    #                 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09', 'OCT':'10',
    #                 'NOV':'11', 'DEC':'12'}
    
    # MonthEnds = ['JAN 31', 'FEB 28', 'MAR 31', 'APR 30', 'MAY 31', 'JUN 30',
    #              'JUL 31', 'AUG 31', 'SEP 30', 'OCT 31', 'NOV 30', 'DEC 31']
    
    link = f'http://microclimates.org/forecast/{Station}'
    # Read into HTML format
    html = request.urlopen(link).read()
    # Parse HTML
    soup = BeautifulSoup(html,'html.parser')
    # Get the text
    Text = soup.text
    
    Page = Text.split('\n\n\n')
    # Find where the row with the latest forecast is
    Border = np.where(np.array(Page) == 'Date\nModel Run')[0][0]
    # Get the string of the date
    RecDate = Page[Border+1].replace('\n', ' ')
    
    Date = pd.to_datetime(Today)
    PrevDate = Date - pd.Timedelta(1, unit='d')
    ForwDate = Date + pd.Timedelta(1, unit='d')

    # Trigger to fix change in month issue
    EndTrigger = False
    if PrevDate.month < Date.month:
        EndTrigger = True
        
    StartTrigger = False
    if ForwDate.month < Date.month:
        StartTrigger = True
    
    WebDay = Date.day
    WebPrevDay = PrevDate.day
    if WebDay < 10:
        WebDay = '0' + str(WebDay)
    if WebPrevDay < 10:
        WebPrevDay = '0' + str(WebPrevDay)
    
    Links = [f"http://microclimates.org/forecast/{Station}/{Date.year}{Date.month}{WebDay}_22.html",
             f"http://microclimates.org/forecast/{Station}/{Date.year}{Date.month}{WebDay}_12.html",
             f"http://microclimates.org/forecast/{Station}/{PrevDate.year}{PrevDate.month}{WebPrevDay}_22.html"]
    
    Results = []
    
    if '2200' not in RecDate:
        del Links[0]
    
    for link in Links:
        # Read into HTML format
        html = request.urlopen(link).read()
        # Parse HTML
        soup = BeautifulSoup(html,'html.parser')
        # Get the text
        Text = soup.text
        
        # Get every row of values
        Tabled = Text.split('\n\n\n')[3:-3]
        
        # Need to clean and put into dataframe
        CleanTable = []
        
        BigDay, BigMonth = Tabled[0].replace('\n', ' ').split(' ')[:2]
        
        for l in Tabled:
            # Split into values
            Values = l.replace(' ', '\n').split('\n')
            
            if '' in Values:
                Values.remove('')
                
            # Hour and date, precip
            if len(Values) == 12:
                Day, Month = Values[:2]
                BigDay = Day
                BigMonth = Month
            
            # Hour and date, no precip
            if len(Values) == 11:
                Day, Month = Values[:2]
                BigDay = Day
                BigMonth = Month
                Values.append('0')
                
            # Hour only, precip value given
            if len(Values) == 10:
                Values.insert(0, BigMonth)
                Values.insert(0, BigDay)
        
            # Hour only, no precip
            if len(Values) == 9:
                Values.insert(0, BigMonth)
                Values.insert(0, BigDay)
                Values.append('0')
            
            CleanTable.append(Values)
        
        VarNames = ['Day', 'Month', 'Hour', 'Temperature [F]', 'DewPoint [F]', 'RH',
                    'Tsoil [F]', 'Wind Dir', 'Wind Speed [kts]', 'Sky Cover (%)',
                    'Net Rad [Wm^-2]', 'Precip [in]']
        
        USLFore = pd.DataFrame(CleanTable, columns=VarNames)
        # Converting to correct type
        USLFore['Temperature [F]'] = USLFore['Temperature [F]'].astype(int)
        USLFore['Wind Speed [kts]'] = USLFore['Wind Speed [kts]'].astype(int)
        USLFore['Precip [in]'] = USLFore['Precip [in]'].astype(float)
        
        # Creating timestamp column
        Timestamp = str(Date.year)+' '+USLFore['Month']+' '+USLFore['Day']+' '+USLFore['Hour']
        # Set timestamp as index
        USLFore.index = pd.to_datetime(Timestamp, format='%Y %b %d %H00')
        # Remove superfluous columns
        USLFore = USLFore.drop(columns=['Hour', 'Day', 'Month', 'DewPoint [F]',
                                        'RH', 'Tsoil [F]', 'Wind Dir',
                                        'Sky Cover (%)', 'Net Rad [Wm^-2]'])
        
        # Get the max/min/wind/precip forecast, bottom of the page
        index1 = Text.find('Total Precip')
        index2 = Text.find('Copyright')
    
        Relevant = Text[index1+12:index2].strip().split('\n')
    
        MaxT = int(Relevant[0].strip('°F'))
        MinT = int(Relevant[1].strip('°F'))
        Wind = int(Relevant[2].strip('kts'))
        Precip = float(Relevant[3].strip('"'))
        
        Results.append([USLFore, np.array([MaxT, MinT, Wind, Precip])])
    
    # Address changing month issue
    if EndTrigger == True:
        Results[2][0].index += pd.DateOffset(months=1)

    if StartTrigger == True:
        Results[0][0].index += pd.DateOffset(months=1)
        Results[1][0].index += pd.DateOffset(months=1)
        NewInds = Results[2][0].index[18:] + pd.DateOffset(months=1)
        Results[2][0].index = list(Results[2][0].index[:18]) + list(NewInds)
    
    return Results


# =============================================================================
# Get NWS Forecast Data
# =============================================================================

def NWSData(Station, TimeShift):
    # Read in observation data from NWS API URL
    link = f"https://api.weather.gov/stations/{Station}/observations"
    # Read into HTML format
    html = request.urlopen(link).read()
    # Parse HTML
    soup = BeautifulSoup(html,'html.parser')
    # Convert to JSON
    site_json = json.loads(soup.text)
    # Extract the latitude and longitude of the station
    Lon, Lat = site_json['features'][0]['geometry']['coordinates']
    # Read in page that will direct us to the forecast for that location
    link = f"https://api.weather.gov/points/{Lat},{Lon}"
    # Read into HTML format
    html = request.urlopen(link).read()
    # Parse HTML
    soup = BeautifulSoup(html,'html.parser')
    # Convert to JSON
    site_json = json.loads(soup.text)
    # Get the actual forecast data page
    link = site_json['properties']['forecastHourly']
    # Read into HTML format
    html = request.urlopen(link).read()
    # Parse HTML
    soup = BeautifulSoup(html,'html.parser')
    # Convert to JSON
    site_json = json.loads(soup.text)
    
    # Set up measurements, not all necessary for now
    Values = {'Temp. [F]':[], 'Time':[], 'WindSpeed [mph]':[]}
    
    # Within "features" is a dictionary for every observation point in time
    # up until a certain timestamp. Append each.
    for i in range(len(site_json['properties']['periods'])):
        
        Data = site_json['properties']['periods'][i]
        # Temperature is in Fahrenheit. Great.
        Values['Temp. [F]'].append(Data['temperature'])
        # Wind speed is in mph
        Values['WindSpeed [mph]'].append(int(Data['windSpeed'].split(' ')[0]))
        # Use the end time as the timestamp
        TimeComps = Data['endTime'].split('-')
        LocalTime = pd.to_datetime('-'.join(TimeComps[:-1]))
        # Get the UTC time
        UTCTime = LocalTime + pd.to_timedelta(TimeShift, unit='h')
        Values['Time'].append(UTCTime)
        
    # Convert dictionary to pandas dataframe
    NWSFore = pd.DataFrame.from_dict(Values).set_index('Time')
    # Covert units where needed
    NWSFore['Wind [kts]'] = NWSFore['WindSpeed [mph]']/1.151
    # Drop superfluous column
    NWSFore = NWSFore.drop(columns=['WindSpeed [mph]'])

    return NWSFore


# =============================================================================
# 
# =============================================================================

def GetLatestHr(Model, Today):
    
    # Get current UTC time as all models work on UTC
    NowUTC = datetime.now(timezone.utc)
    # Get tomorrow's and yesterday's date (not UTC based)
    Tomorrow = (pd.to_datetime(Today) + pd.Timedelta(1, unit='d')).date().strftime('%Y-%m-%d')
    Yesterday = (pd.to_datetime(Today) - pd.to_timedelta(1, unit='d')).strftime('%Y-%m-%d')

    # Find the timedelta with every 4 hours on the same day and the day before
    # Select whichever has the negative delta closest to zero
    
    if Model in ['gfs', 'gefs', 'nam', 'ecmwf']:
        Times = [pd.to_datetime(Yesterday + ' 00:00'), pd.to_datetime(Yesterday + ' 06:00'),
                 pd.to_datetime(Yesterday + ' 12:00'), pd.to_datetime(Yesterday + ' 18:00'),
                 pd.to_datetime(Today + ' 00:00'), pd.to_datetime(Today + ' 06:00'),
                 pd.to_datetime(Today + ' 12:00'), pd.to_datetime(Today + ' 18:00'),
                 pd.to_datetime(Tomorrow + ' 00:00'), pd.to_datetime(Tomorrow + ' 06:00'),
                 pd.to_datetime(Tomorrow + ' 12:00'), pd.to_datetime(Tomorrow + ' 18:00')]
        
        Deltas = np.zeros(len(Times))
        for t in range(len(Times)):
            Deltas[t] = ((Times[t].tz_localize('UTC') - NowUTC)/np.timedelta64(1, 'h'))
        
        Smallest = np.argmax(Deltas[Deltas < 0])
        if Deltas[Deltas < 0][Smallest] < -3:
            LastUpdate = Times[Smallest].replace(tzinfo=None)
        else:
            LastUpdate = Times[Smallest-3].replace(tzinfo=None)
        
    if Model == 'nbm':
        Times = [pd.to_datetime(Yesterday + ' 00:00'), pd.to_datetime(Yesterday + ' 12:00'), 
                 pd.to_datetime(Today + ' 00:00'), pd.to_datetime(Today + ' 12:00'), 
                 pd.to_datetime(Tomorrow + ' 00:00'), pd.to_datetime(Tomorrow + ' 12:00')]

        Deltas = np.zeros(len(Times))
        for t in range(len(Times)):
            Deltas[t] = ((Times[t].tz_localize('UTC') - NowUTC)/np.timedelta64(1, 'h'))
    
        Smallest = np.argmax(Deltas[Deltas < 0])
        if Deltas[Deltas < 0][Smallest] < -3:
            LastUpdate = Times[Smallest].replace(tzinfo=None)
        else:
            LastUpdate = Times[Smallest-3].replace(tzinfo=None)
    
    if Model == 'hrrr':
        LastUpdate = pd.to_datetime(NowUTC).floor('2h').replace(tzinfo=None)
    
    return LastUpdate


# =============================================================================
# 
# =============================================================================

VarDict = {'gfs':[":TMP:2 m above ground:", ":[U|V]GRD:10 m above ground:", ":APCP:surface:"],
           'nam':[":TMP:2 m above ground:", ":[U|V]GRD:10 m above ground:", ":APCP:surface:"],
           'hrrr':[":TMP:2 m above ground:", ":[U|V]GRD:10 m above ground:", ":APCP:surface:"],
           'nbm':[":TMP:2 m above ground:", ":WIND:10 m above ground:", ":APCP:surface:"],
           'ecmwf':[":2t:", ":10[u|v]:", ":tp:"],
           'gefs':[":TMP:2 m above ground:", ":[U|V]GRD:10 m above ground:", ":APCP:surface:"]}

def ModelOutput(Models, Date, Latitude, Longitude, Code, UTC, units=0):
    
    # List of models currently included:
    # NAM, GFS, HRRR, NBM, ECMWF, GEFS
    # HRRR - Every hour - 1h dt
    # GFS - 00/06/12/18 - 3h dt
    # GEFS - 00/06/12/18 
    # NAM - 00/06/12/18 - 3h dt
    # ECMWF - 00/12 - 3h dt
    # nbm - 00/12 - 1h dt

    # Set latitude and longitude
    Point = pd.DataFrame({'longitude': [Longitude],
                          'latitude': [Latitude]})
 
    Today2 = datetime.today().strftime('%Y-%m-%d').replace('-', '')
    
    Output = {}
    
    for Name in Models:
        
        m = Name.split()[0]
        Hour = Name.split()[1] + ':00'
        
        if int(Name.split()[1]) == 18:
            if UTC == 5:
                StartHour = 12
                FinHour = 36
                
            if UTC == 4:
                StartHour = 11
                FinHour = 35
            
        if int(Name.split()[1]) == 12:
            if UTC == 5:
                StartHour = 18
                FinHour = 42
            
            if UTC == 4:
                StartHour = 17
                FinHour = 41
        
        ConvDate = [pd.to_datetime(Date + f' {Hour}')]
        
        print(f'Getting {m.upper()} {Hour}Z data...')
                
        try:
            if m == 'nbm':
                # Set forecast time
                fxx = range(StartHour, FinHour)
                H = FastHerbie(ConvDate, model=m, fxx=fxx, product='co')
            
            elif m == 'gfs':
                fxx = range(StartHour, FinHour, 3)
                H = FastHerbie(ConvDate, model=m, fxx=fxx)
                
            elif m == 'nam':
                fxx = range(StartHour, FinHour, 3)
                H = FastHerbie(ConvDate, model=m, fxx=fxx)
            
            elif m == 'gefs':
                fxx = range(StartHour, FinHour, 3)
                H = FastHerbie(ConvDate, model=m, product="atmos.25", 
                               member='avg', fxx=fxx)
        
            elif m == 'ecmwf':
                fxx = range(StartHour, FinHour, 3)
                H = FastHerbie(ConvDate, model=m, product="oper", fxx=fxx)
            
            elif m == 'hrrr':
                fxx = range(StartHour, FinHour)
                H = FastHerbie(ConvDate, model=m, fxx=fxx)
        
            # Collect variables: temperature, windspeed, precipitation
            ds1 = H.xarray(VarDict[m][0])
            ds2 = H.xarray(VarDict[m][1])
            ds3 = H.xarray(VarDict[m][2])
            
            # Put all in one
            if m == 'nbm':
                ds1['wind'] = ds2['si10']
            else:
                ds1['wind'] = np.sqrt(ds2['u10']**2 + ds2['v10']**2)
            
            ds1['tp'] = ds3.tp
            # Get variables only for the point
            dsi = ds1.herbie.pick_points(Point)
            
            if units == 0:
                ModRez = pd.DataFrame({'Time':dsi['valid_time'].values, 
                                       'Temp. [F]':dsi['t2m'].values.flatten(),
                                       'Wind [kts]':dsi['wind'].values.flatten(), 
                                       'Precip [in]':dsi['tp'].values.flatten()})
            
                # Convert to Fahrenheit, knots, and inches  
                ModRez['Temp. [F]'] = (ModRez['Temp. [F]']-273.15)*(9/5) + 32
                ModRez['Wind [kts]'] *= 1.944
                ModRez['Precip [in]'] *= 1/25.4
            
            if units == 1:
                ModRez = pd.DataFrame({'Time':dsi['valid_time'].values, 
                                       'Temperature [C]':dsi['t2m'].values.flatten(),
                                       'Wind Speed [m/s]':dsi['wind'].values.flatten(), 
                                       'Precipitation [mm]':dsi['tp'].values.flatten()})
            
                # Convert to Fahrenheit, knots, and inches  
                ModRez['Temperature [C]'] = (ModRez['Temperature [C]']-273.15)
                
            # Set time as index
            ModRez = ModRez.set_index('Time')
            
        except:
            print(f'{m} data could not be attained.')
            ModRez = pd.DataFrame(columns=['Time', 'Temp. [F]', 'Wind [kts]',
                                           'Precip [in]'])
            
        Output[m] = ModRez
    
    # Save the dictionary of dataframes as a pickle object    
    with open(f'Data/US_ModelData/USMods_{Code}_{Today2}.pickle', 'wb') as f:
        pickle.dump(Output, f)
    
    return Output


# =============================================================================
# 
# =============================================================================

def ECStationData(Code, UTC):
    
    # Today's date
    Today1 = datetime.today().strftime('%Y-%m-%d')
    Today2 = datetime.today().strftime('%Y-%m-%d').replace('-', '')
    # I hate this UTC thing
    Tomorrow1 = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    Tomorrow2 = Tomorrow1.replace('-', '')

    # Check if file already exists
    try:
        # If it exists, load it
        OrgFile = pd.read_csv(f'Data/EC_StationData/{Code}_{Today2}.csv', 
                              index_col=0)

    except:
        # If not, create empty DataFrame
        OrgFile = pd.DataFrame(columns=['Time', 'Temperature [C]', 'Wind Speed [m/s]', 
                                        'Wind Direction [deg]','Precipitation [mm]',
                                        'URL'])

    # Main MSC Datamart link
    Sources = {'Today':[Today1, Today2, 
               f'https://dd.weather.gc.ca/{Today2}/WXO-DD/observations/swob-ml/'],
               'Tomorrow':[Tomorrow1, Tomorrow2,
               f'https://dd.weather.gc.ca/{Tomorrow2}/WXO-DD/observations/swob-ml/']}

    # Prepare for dataframing
    ObsData = []

    # List to prevent line overflow
    Ss = ['om:ObservationCollection', 'om:member', 'om:Observation', 'om:result', 
          'elements', 'element', 'om:samplingTime', 'gml:TimeInstant', 
          'gml:timePosition']

    AllStamps = []

    # Check if it's tomorrow yet (don't think about this sentence too hard)
    TimeNow = datetime.today().hour
    if TimeNow < 24 - UTC:
        # If not after 7pm in Montreal, tomorrow hasn't happened yet
        del Sources['Tomorrow']

    for s in Sources.keys():
        # Link containing all the xml files of the day
        AllFiles = Sources[s][2] + Sources[s][1] + f'/{Code}/'
        # Read into HTML format
        html = request.urlopen(AllFiles).read()
        # Parse HTML
        soup = BeautifulSoup(html,'html.parser')
        # Convert to... list?
        Lines = list(str(soup).split('\n'))
        Timestamps = []
        for l in Lines:
            if Sources[s][0] in l:
                Stamp = re.findall('"([^"]*)"', l)[2]
                if ('minute' in Stamp) and (Stamp not in OrgFile['URL'].values):
                    # Get UTC time, 4 or 5 hour difference
                    Hr = int(l[64:66])
                    if (s == 'Tomorrow') and (Hr < UTC):
                        Timestamps.append(Stamp)
                        AllStamps.append(Stamp)
                        
                    if (s == 'Today') and (Hr >= UTC):
                        Timestamps.append(Stamp)
                        AllStamps.append(Stamp)

        print(f'Reading in observation data from {s.lower()}...')
        for t in Timestamps:
            data = xmltodict.parse(request.urlopen(AllFiles+t).read())
            # Dictionary with data
            Values = data[Ss[0]][Ss[1]][Ss[2]][Ss[3]][Ss[4]][Ss[5]]
            # Sampling time in UTC (str)
            Time = data[Ss[0]][Ss[1]][Ss[2]][Ss[6]][Ss[7]][Ss[8]]
            
            # Collect air temperature, wind speed, wind direction, and precipitation
            TempC = Values[4]['@value']  # Celsius
            WindS = Values[8]['@value']  # km/h
            WindD = Values[9]['@value']  # degrees
            PrecT = Values[47]['@value'] # mm
        
            ObsData.append([Time, TempC, WindS, WindD, PrecT])
            
            print(r'{0}'.format(t), end='\r')
    
    print('')
    ObsData = pd.DataFrame(ObsData, columns=['Time', 'Temperature [C]',
                                             'Wind Speed [m/s]', 
                                             'Wind Direction [deg]',
                                             'Precipitation [mm]'])

    # Replace missing values with NaN
    ObsData = ObsData.replace('MSNG', np.nan)
    # Convert time to datetime object
    ObsData['Time'] = pd.to_datetime(ObsData['Time'])
    # Convert values to floats
    ObsData.iloc[:,1:] = ObsData.iloc[:,1:].astype(float)
    # Convert wind to m/s 
    ObsData['Wind Speed [m/s]'] *= 1/3.6
    # Set new index
    ObsData = ObsData.set_index('Time')
    # Add URL column
    ObsData['URL'] = AllStamps

    if OrgFile.shape[0] > 0:
        ToOutput = pd.concat([OrgFile, ObsData])
    else:
        ToOutput = ObsData

    ToOutput.to_csv(f'Data/EC_StationData/{Code}_{Today2}.csv')    

    return ToOutput


# =============================================================================
# 
# =============================================================================

def ECDataChecker():

    Yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d').replace('-', '')
    
    YesterLinks = {'gdps':f'https://dd.weather.gc.ca/{Yesterday}/WXO-DD/model_gem_global/15km/grib2/lat_lon/12/003/',
                  'rdps':f'https://dd.weather.gc.ca/{Yesterday}/WXO-DD/model_gem_regional/10km/grib2/18/003/',
                  'hrdps':f'https://dd.weather.gc.ca/{Yesterday}/WXO-DD/model_hrdps/continental/2.5km/18/003/'}
    
    Hours = {'gdps':'ZZ', 'rdps':'ZZ', 'hrdps':'ZZ'}
    
    for m in YesterLinks.keys():
        # for t in Links[m][1]:
        # Read into HTML format
        try:
            html = request.urlopen(YesterLinks[m]).read()
            # Parse HTML
            soup = BeautifulSoup(html,'html.parser')
            # Convert to... list?
            Lines = list(str(soup).split('\n'))
            # Basic check: an empty HRDPS folder had 13 lines.
            if len(Lines) > 13:
                Hours[m] = YesterLinks[m][-7:-5]
        except:
            print(f'{m} is missing data.')

    return Hours


# =============================================================================
# 
# =============================================================================

def CanadianModels(Latitude, Longitude, Code, UTC):

    # Set latitude and longitude
    Point = pd.DataFrame({'longitude': [Longitude],
                          'latitude': [Latitude]})


    # Dictionary to append the data to
    Everything = {'rdps':[], 'hrdps':[], 'gdps':[]}

    Today = datetime.today().strftime('%Y-%m-%d')
    TodayAlt = Today.replace('-', '')

    Date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    Date2 = Date.replace('-', '')

    URLs = {'rdps':f'https://dd.weather.gc.ca/{Date2}/WXO-DD/model_gem_regional/10km/grib2/18/',
            'gdps':f'https://dd.weather.gc.ca/{Date2}/WXO-DD/model_gem_global/15km/grib2/lat_lon/12/',
            'hrdps':f'https://dd.weather.gc.ca/{Date2}/WXO-DD/model_hrdps/continental/2.5km/18/'}

    Filenames = {'rdps':{'T':'*CMC_reg_TMP*.grib2', 'U':'*CMC_reg_UGRD*.grib2',
                         'V':'*CMC_reg_VGRD*.grib2', 'P':'*CMC_reg_APCP*.grib2'},
                 'gdps':{'T':'*CMC_glb_TMP*.grib2', 'U':'*CMC_glb_UGRD*.grib2',
                         'V':'*CMC_glb_VGRD*.grib2', 'P':'*CMC_glb_APCP*.grib2'},
                 'hrdps':{'T':'*HRDPS_TMP*.grib2', 'U':'*HRDPS_UGRD*.grib2',
                          'V':'*HRDPS_VGRD*.grib2', 'P':'*HRDPS_APCP*.grib2'}}

    # Check which ones have data
    Cycles = ECDataChecker()
    
    if UTC == 5:
        fxxs = {'rdps':np.arange(12, 36), 'gdps':np.arange(18, 42, 3),
                'hrdps':np.arange(12, 36)}

    if UTC == 4:
        fxxs = {'rdps':np.arange(11, 35), 'gdps':np.arange(17, 41, 3),
                'hrdps':np.arange(11, 35)}


    for m in Everything.keys():
        if Cycles[m] == 'ZZ':
            print(f'Data for {m} could not be attained.')
            continue
        
        for x in fxxs[m]:
            
            # Define the string of the model step
            strfxstep = str(x)
            if len(strfxstep) == 1:
                fxstep = f'00{strfxstep}'
            if len(strfxstep) == 2:
                fxstep = f'0{strfxstep}'
            if len(strfxstep) == 3:
                fxstep = strfxstep
        
            # Define the names of the files by variable and model
            TmpFile = {'rdps':f'CMC_reg_TMP_TGL_2_ps10km_{Date2}18_P{fxstep}.grib2',
                       'gdps':f'CMC_glb_TMP_TGL_2_latlon.15x.15_{Date2}12_P{fxstep}.grib2',
                       'hrdps':f'{Date2}T18Z_MSC_HRDPS_TMP_AGL-2m_RLatLon0.0225_PT{fxstep}H.grib2'}
            
            UwFile = {'rdps':f'CMC_reg_UGRD_TGL_10_ps10km_{Date2}18_P{fxstep}.grib2',
                       'gdps':f'CMC_glb_UGRD_TGL_10_latlon.15x.15_{Date2}12_P{fxstep}.grib2',
                       'hrdps':f'{Date2}T18Z_MSC_HRDPS_UGRD_AGL-10m_RLatLon0.0225_PT{fxstep}H.grib2'}
            
            VwFile = {'rdps':f'CMC_reg_VGRD_TGL_10_ps10km_{Date2}18_P{fxstep}.grib2',
                       'gdps':f'CMC_glb_VGRD_TGL_10_latlon.15x.15_{Date2}12_P{fxstep}.grib2',
                       'hrdps':f'{Date2}T18Z_MSC_HRDPS_VGRD_AGL-10m_RLatLon0.0225_PT{fxstep}H.grib2'}
            
            PrcFile = {'rdps':f'CMC_reg_APCP_SFC_0_ps10km_{Date2}18_P{fxstep}.grib2',
                       'gdps':f'CMC_glb_APCP_SFC_0_latlon.15x.15_{Date2}12_P{fxstep}.grib2',
                       'hrdps':f'{Date2}T18Z_MSC_HRDPS_APCP_Sfc_RLatLon0.0225_PT{fxstep}H.grib2'}
            
            # PRate = {'hrdps':f'{Date2}T18Z_MSC_HRDPS_PRATE_Sfc_RLatLon0.0225_PT{fxstep}H.grib2'}
            
            # Download all the grib files
            urllib.request.urlretrieve(URLs[m]+fxstep+'/'+TmpFile[m], 'Temporary/'+TmpFile[m])
            urllib.request.urlretrieve(URLs[m]+fxstep+'/'+UwFile[m], 'Temporary/'+UwFile[m])
            urllib.request.urlretrieve(URLs[m]+fxstep+'/'+VwFile[m], 'Temporary/'+VwFile[m])
            urllib.request.urlretrieve(URLs[m]+fxstep+'/'+PrcFile[m], 'Temporary/'+PrcFile[m])
        
            print(r'Downloading {0} Hour {1}'.format(m, x), end='\r')

        print('')
        print(f'Loading {m} files...')
        # Lists of all the filenames by variable
        TFiles = glob.glob(f"Temporary/{Filenames[m]['T']}")
        UFiles = glob.glob(f"Temporary/{Filenames[m]['U']}")
        VFiles = glob.glob(f"Temporary/{Filenames[m]['V']}")
        PFiles = glob.glob(f"Temporary/{Filenames[m]['P']}")
                
        # Load the datasets
        dsT = xr.open_mfdataset(TFiles, engine='cfgrib', 
                                 combine='nested', concat_dim='step')
        
        dsU = xr.open_mfdataset(UFiles, engine='cfgrib', 
                                 combine='nested', concat_dim='step')
        
        dsV = xr.open_mfdataset(VFiles, engine='cfgrib', 
                                 combine='nested', concat_dim='step')
        
        dsP = xr.open_mfdataset(PFiles, engine='cfgrib', 
                                 combine='nested', concat_dim='step')
        
        dsT['u10'] = dsU.u10
        dsT['v10'] = dsV.v10
        dsT['tp'] = dsP.unknown
        
        # Set the tree name (once is enough)
        if m != 'gdps':
            TreeName = f'{m}_{dsT.longitude.shape[1]}_{dsT.longitude.shape[0]}'
        else:
            TreeName = f'{m}_{dsT.longitude.shape[0]}_{dsT.latitude.shape[0]}'
        
        # Get station's location
        dsi = dsT.herbie.pick_points(Point, tree_name=TreeName)
        # Extract the values (unfortunately slow)
        ModRez = pd.DataFrame({'Time':dsi['valid_time'].values, 
                               'Temperature [C]':dsi['t2m'].values.flatten(),
                               'U10':dsi['u10'].values.flatten(),
                               'V10':dsi['v10'].values.flatten(),
                               'Precipitation [mm]':dsi['tp'].values.flatten()})
        
        Everything[m] = ModRez
        
        # Convert to Celsius
        Everything[m]['Temperature [C]'] += -273.15
        
        # Get wind-speed and wind-direction from u,v components
        Everything[m]['Wind Speed [m/s]'] = np.sqrt(Everything[m]['U10']**2 +\
                                                    Everything[m]['V10']**2)
        Everything[m]['Wind Direction [deg]'] = (270 - np.arctan2(Everything[m]['V10'],
                                                  Everything[m]['U10'])*180/np.pi) % 360
        
        # Drop u10, v10
        Everything[m] = Everything[m].drop(['U10', 'V10'], axis=1)
        
        # Set index
        Everything[m] = Everything[m].set_index('Time')
        
        # Delete all the files before moving on to next model
        AllFiles = glob.glob('Temporary/*')
        for f in AllFiles:
            os.remove(f)
    
    # Save a dictionary of dataframes as a pickle object
    with open(f'Data/EC_ModelData/ECMods_{Code}_{TodayAlt}.pickle', 'wb') as f:
        pickle.dump(Everything, f)
    
    return Everything
    

# =============================================================================
# 
# =============================================================================

def ECRadarGetter(Radar):
    
    Today = datetime.today().strftime('%Y-%m-%d')
    TodayAlt = Today.replace('-', '')
    
    # URL of the data center
    URL = f'https://dd.weather.gc.ca/{TodayAlt}/WXO-DD/radar/DPQPE/GIF/{Radar}/'
    # List to hold image file names
    Files = []
    # Read into HTML format
    html = request.urlopen(URL).read()
    # Parse HTML
    soup = BeautifulSoup(html,'html.parser')
    # Convert to list
    Lines = list(str(soup).split('\n'))
    for l in range(len(Lines)):
        # Take only rain for now
        if 'Rain.gif' in Lines[l]:
            # Get the URL part only
            Stamp = re.findall('"([^"]*)"', Lines[l])[2]
            # Assume 5 hr difference with UTC
            Hr = int(Stamp[9:11])
            if Hr > 5:
                Files.append('Temporary/'+Stamp)
    
            # Download
            urllib.request.urlretrieve(URL+Stamp, 'Temporary/'+Stamp)
        
        print(r'Downloading Radar Image {0}'.format(l), end='\r')
    
    print('')
    
    NewWidth = 800
    
    print('Resizing...')
    # Resize all the images
    for filename in Files:
        # Stolen from https://gist.github.com/tomvon/ae288482869b495201a0
        img = Image.open(filename)
        wpercent = (NewWidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((NewWidth, hsize), PIL.Image.BICUBIC)
        img.save(filename)
    
    print('')
    
    # Combine images into a GIF
    with imageio.get_writer(f'Figures/{Radar}_{TodayAlt}.gif',
                            mode='I', duration=100) as writer:
        for filename in Files:
            image = imageio.imread(filename)
            writer.append_data(image)
    
    # Delete all the images
    for filename in os.listdir('Temporary'):
        os.remove('Temporary/'+filename)

    return

# wpercent = (800/float(580))
# hsize = int((float(480)*float(wpercent)))

# =============================================================================
# 
# =============================================================================

def HRDPSRainGetter(RadName, RadLat, RadLon):
    
    # Today's date
    Today = datetime.today().strftime('%Y-%m-%d')
    TodayAlt = Today.replace('-', '')
    
    # Yesterday's date
    Date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    Date2 = Date.replace('-', '')
    
    # Url from the datamart
    URL = f'https://dd.weather.gc.ca/{Date2}/WXO-DD/model_hrdps/continental/2.5km/18/'
    # File name style
    Filenames = '*HRDPS_PRATE*.grib2'
    # Hours to get data for
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
        
        # The filename
        PRate = f'{Date2}T18Z_MSC_HRDPS_PRATE_Sfc_RLatLon0.0225_PT{fxstep}H.grib2'
        
        # Download all the grib files
        urllib.request.urlretrieve(URL+fxstep+'/'+PRate, 'Temporary/'+PRate)
    
        print(r'Downloading HRDPS Hour {0}'.format(x), end='\r')
    
    print('')
    print('Loading HRDPS files...')
    # List of all the filenames by variable
    PFiles = glob.glob(f"Temporary/{Filenames}")
    
    # Load the dataset
    dsP = xr.open_mfdataset(PFiles, engine='cfgrib', 
                             combine='nested', concat_dim='step')
    
    # Get latitude, longitude, and convert initial values
    Lats = dsP.latitude.values
    Lons = dsP.longitude.values
    Pras = dsP.prate.values*86400
    Pras[Pras == 0] = np.nan
    Timestamps = pd.to_datetime(dsP.valid_time.values - pd.to_timedelta(5, unit='h'))

    # Province borders, from sienna22 on stack exchange
    states_provinces = cfeature.NaturalEarthFeature(category='cultural', 
            name='admin_1_states_provinces_lines', scale='50m', facecolor='none')
    
    # Value levels more or less matching ECCC radar plots
    Levels = np.array([0, 0.1, 1, 2, 5, 10, 25, 50, 100, 200, 300])
    
    
    # Approximate deltas from RadLon, RadLat to get the plot extent
    NoSo = 250/110
    EaWe = 330/110
    
    # Create a discretized colormap based on 'jet'
    cmap = plt.cm.get_cmap('jet', len(Levels)+1)
    # Match levels to the colormap
    norm = BoundaryNorm(Levels, cmap.N, extend='both')
    # List to hold the filenames of the images
    Filenames = []
    
    for x in range(Pras.shape[0]):
    
        Fig = plt.figure(figsize=(8.0, 6.62), dpi=100)
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_title(f"{Timestamps[x].strftime('%Y-%m-%d %H:00')} LT", fontsize=15)
        # ax.set_title(str(dsP.valid_time.values[x]).split('T')[1][:5] + ' UTC')
        ax.set_extent([RadLon-EaWe, RadLon+EaWe, RadLat-NoSo, RadLat+NoSo])
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(states_provinces, edgecolor='black', linestyle='dashed')
        
        rain = ax.contourf(Lons, Lats, Pras[x]/24, cmap=cmap, levels=Levels, norm=norm, extend='both')
        
        ax.add_feature(cfeature.LAKES, edgecolor='k', linewidth=0.3)
        
        ax.scatter(-73.579185, 45.504926, marker='*', edgecolor='k', 
                   facecolor='red', s=200, zorder=10)
        
        ax.scatter(RadLon, RadLat, marker='+', color='grey', s=200, zorder=10)
            
        cbar = Fig.colorbar(rain, ax=ax, orientation='vertical', location='right',
                              fraction=0.1, pad=0.05, shrink=0.75, ticks=Levels)
        cbar.set_label('Precipitation Rate [mm/hr]',
                        fontsize=12)
        
        plt.tight_layout()
        plt.savefig(f'Temporary/Hrdps_{TodayAlt}_{x+1}_Rain.png')
        Filenames.append(f'Temporary/Hrdps_{TodayAlt}_{x+1}_Rain.png')
        plt.close()    
    
    # Combine images into a GIF
    with imageio.get_writer(f'Figures/HRDPS_{RadName}_{TodayAlt}.gif',
                            mode='I', duration=250) as writer:
        for filename in Filenames:
            image = imageio.imread(filename)
            writer.append_data(image)
    
    # Delete all the files and images
    for filename in os.listdir('Temporary'):
        os.remove('Temporary/'+filename)
        
    return