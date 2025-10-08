Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Monitor {
    [DllImport("user32.dll", CharSet=CharSet.Auto)]
    public static extern IntPtr SendMessage(IntPtr hWnd, int msg, IntPtr wParam, IntPtr lParam);
}
"@
[Monitor]::SendMessage([IntPtr]::Zero, 0x0112, [IntPtr]0xF170, [IntPtr]2)