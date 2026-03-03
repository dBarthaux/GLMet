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

## GLMet - A Brief History and Origin Story
In Fall 2024 I was guilted into participating in the yearly "WxChallenge", a weather forecasting tournament for university students and alumni. The other more experienced forecasters in my department had impressive worklflows and data sources.
They gave me a list of websites to analyze model output, radars, official forecasts, etc. I was quite frankly nonplussed about the whole ordeal and frequently resorted to the "ballpark it" method of forecasting. Yes, I may have cost my team several
key points along the way. But if you find me in their data, you would see that I wasn't the worst forecaster on the team.

At some point I started wondering - as anyone would - if there was any way I could beat the models and maybe see how much the forecasters had improved over the years of this challenge. After a lot of data-dowloading, line-fitting, and code-writing, I got nowhere.
It turns out you can't just average the model forecasts in such a way that you can outperform them on average. Wow. Shocker.

At that point in the school year I had already fallen quite behind my peers, and any attempt at developing a forecasting linear regression to gain back the lead would've been futile. However, I had enjoyed the fact that I could now just hit F5 in Spyder and the relevant
plots, data tables, and model forecasts would quaintly pop up on my screen. So I continued to fiddle with that until I got most of the functions you see in CanadaMart. I then tailored it so that the forecasts were for a specific point near a Canadian weather radar. I
realized the department had a spare TV laying around (it was replaced by this behemoth of a monitor), and I said to myself: "How nice would it be if we could come in to the grad lounge and see this data compared to the observations?". So I set up the automatic updater,
the AutoHotKeys, and the JPEGViewer slideshow.

Everything was fine for about two months. People would come in, occasionally glance at the temperature figure and radar animation, say "man our wind measurements suck, eh?" then leave with their coffee. But one day, what I can only describe as a "departmental mutiny" occurred,
lead by a fellow grad student. They stated their demands, pure and simple: We Want Bears. Who cares about the weather - we want to see Kodiak bears ripping salmon apart with their teeth. I fought tooth and claw, but ultimately I relented and gave the people what they wanted.
I made it so that the TV would show the livestream in Chrome with a news ticker at the bottom listing some weather information ("NewsVideo.py"), and then some inane headlines (TextCrawl.txt") that I updated once a week. Once the bears went into hibernation, it all stopped.
