Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Move mouse by 1 pixel and back to wake the screen
$pos = [System.Windows.Forms.Cursor]::Position
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point ($pos.X+1), ($pos.Y+1)
[System.Windows.Forms.Cursor]::Position = $pos