' Aadhya WhatsApp Bulker - 24/7 Background Service Launcher
' Launches the server and permanent link completely detached from Antigravity
' Runs silently in the background even if you close Antigravity, VS Code, or browser windows!

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get current directory
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' 1. Start Python Web Server silently in background (0 = hidden, False = detached)
WshShell.Run "python app_web.py", 0, False

' Wait 2 seconds for server to bind
WScript.Sleep 2000

' 2. Start Permanent Ngrok Tunnel silently in background
WshShell.Run "ngrok.exe http 5000", 0, False

' 3. Show confirmation message
WshShell.Popup "Aadhya WhatsApp Bulker is now running 24/7 in Windows background!" & vbCrLf & vbCrLf & _
               "You can safely close Antigravity and any windows." & vbCrLf & _
               "Your permanent link is live: https://buzz-oppressed-ominous.ngrok-free.dev", _
               5, "Aadhya WhatsApp Bulker - Running 24/7", 64
