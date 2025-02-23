@echo on
taskkill /IM JPEGView.exe /F
call C:\Users\meteouser\miniconda3\Scripts\activate.bat
cd C:\Users\meteouser\Documents\GLMet-main
python "CanadaMart.py"

set "folder=C:\Users\meteouser\Documents\GLMet-main\Figures"
for %%F in ("%folder%\*.png") do (
	start "" "C:\Program Files\JPEGView64\JPEGView.exe" "%%F"
	goto :done
)
:done
timeout /t 2 /nobreak
start "" "C:\Users\meteouser\Documents\AutoHotkey\JPEGViewerDoer.exe"