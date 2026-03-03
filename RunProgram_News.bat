@echo on
rem First activate conda console
call C:\Users\meteouser\miniconda3\Scripts\activate.bat

rem Navigate to directory
cd C:\Users\meteouser\Documents\GLMet-main

rem Run the data updater
python "CanadaMart.py"

rem Pause
timeout /t 2 /nobreak

rem Run the HTML script
python "NewsVideo.py"

rem Pause
timeout /t 2 /nobreak

rem Make Chrome full screen
powershell -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{F11}')"

