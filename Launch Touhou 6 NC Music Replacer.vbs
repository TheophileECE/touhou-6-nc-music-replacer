Option Explicit

Dim shell, fso, base, app, cmd, rc
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

base = fso.GetParentFolderName(WScript.ScriptFullName)
app = Chr(34) & base & "\app.pyw" & Chr(34)

If Not fso.FileExists(base & "\app.pyw") Then
    MsgBox "app.pyw was not found next to this launcher.", vbCritical, "Touhou 6 NC Music Replacer"
    WScript.Quit 1
End If

' Prefer the standard Python launcher. WScript keeps its console hidden.
rc = shell.Run("cmd /c where py.exe >nul 2>nul", 0, True)
If rc = 0 Then
    shell.Run "py.exe -3 " & app, 0, False
    WScript.Quit 0
End If

' Fall back to a regular Python executable on PATH.
rc = shell.Run("cmd /c where python.exe >nul 2>nul", 0, True)
If rc = 0 Then
    shell.Run "python.exe " & app, 0, False
    WScript.Quit 0
End If

' Older/install-specific aliases can still expose the windowless executables only.
rc = shell.Run("cmd /c where pyw.exe >nul 2>nul", 0, True)
If rc = 0 Then
    shell.Run "pyw.exe -3 " & app, 0, False
    WScript.Quit 0
End If

rc = shell.Run("cmd /c where pythonw.exe >nul 2>nul", 0, True)
If rc = 0 Then
    shell.Run "pythonw.exe " & app, 0, False
    WScript.Quit 0
End If

MsgBox "Python 3 was not found." & vbCrLf & vbCrLf & _
       "Install Python 3 from python.org and enable 'Add Python to PATH', then launch this file again.", _
       vbExclamation, "Touhou 6 NC Music Replacer"
