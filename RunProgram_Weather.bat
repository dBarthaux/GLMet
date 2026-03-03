@echo on
rem Close JPEGView if open
taskkill /IM JPEGView.exe /F

rem Open a python environment
call C:\Users\meteouser\miniconda3\Scripts\activate.bat

rem Navigate to directory
cd C:\Users\meteouser\Documents\GLMet-main

rem Launch data collection and plot manager
python "CanadaMart.py"

rem Launch JPEGView with the figures folder
set "folder=C:\Users\meteouser\Documents\GLMet-main\Figures"
for %%F in ("%folder%\*.png") do (
	start "" "C:\Program Files\JPEGView64\JPEGView.exe" "%%F"
	goto :done
)
:done

rem Use hotkeys to automatically make fullscreen
timeout /t 2 /nobreak
start "" "C:\Users\meteouser\Documents\AutoHotkey\JPEGViewerDoer.exe"

