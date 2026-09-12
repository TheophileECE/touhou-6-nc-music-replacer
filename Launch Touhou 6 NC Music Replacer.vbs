Option Explicit
Dim shell, fso, base, app, rc
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
app = Chr(34) & base & "\app.pyw" & Chr(34)

rc = shell.Run("cmd /c where pyw.exe >nul 2>nul", 0, True)
If rc = 0 Then
    shell.Run "pyw.exe -3 " & app, 0, False
    WScript.Quit
End If

rc = shell.Run("cmd /c where pythonw.exe >nul 2>nul", 0, True)
If rc = 0 Then
    shell.Run "pythonw.exe " & app, 0, False
    WScript.Quit
End If

MsgBox "Python 3 was not found." & vbCrLf & vbCrLf & _
       "Install Python 3 from python.org and enable 'Add Python to PATH', then launch this file again.", _
       vbExclamation, "Touhou 6 NC Music Replacer"
