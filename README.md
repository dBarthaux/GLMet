# GLMet - A Graduate Lounge Meteorology Data Viewer

This repository is a (primarily) Python-coded fun plotter and updater of observational and model weather data for a local pair of ECCC weather station and radar. It has currently only been tested in Windows.

## How to Run GLMet
Just download the files into a directory, change the paths in the Batch files as needed. You can then run the Batch scripts manually (i.e., double clicking) or setting it to update automatically via Windows Task Scheduler.

If you are intending on running the "RunProgram_News.bat", you will need to either specify a website in loadfuncs.py (line 1077) or amend that function to fit your needs.
You will also have to uncomment the last line in CanadaMart.py.

## What to Change to Fit Your Location

In CanadaMart.py, there is a section of code at the beginning that sets the information on the local ECCC weather/climate station, and the closest weather radar:

> Latitude = 45.504926
> 
> Longitude = -73.579185
> 
> Code = 'CWTA'
> Name = 'McTavish'
> 
> RadName = 'CASBV'
> 
> RadLat = 45.70628
> 
> RadLon = -73.85892

To change it to your location, simply put the latitudes and longitudes of the weather station (first two), then the radar (RadLat, RadLon). Code and RadName must be the official names used by ECCC.
You will also likely have to amend the timezone sections (CanadaMart.py: 46-51, loadfuncs.py: 34-35) if you're not in EST.

## Dependencies
### Python Packages
Herbie - https://github.com/blaylockbk/Herbie

BeautifulSoup

xarray

xmltodict

imageio.v2

cartopy

PIL

### External Programs (only if using Run_Program_Weather.bat)
JPEGView - https://sourceforge.net/projects/jpegview/

AutoHotKey - https://www.autohotkey.com/
