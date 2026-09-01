Attribute VB_Name = "TolStack"
' TolStack add-in module.
' Adds a floating "Open TolStack" button whenever Excel runs with this add-in
' loaded. The button launches the always-on-top TolStack app; the launcher
' pip-installs any missing Python packages on first run.
'
' SCRIPT_DIR is rewritten by Install-TolStack-AddIn.ps1 at install time.

Public Const SCRIPT_DIR As String = "%SCRIPT_DIR%"
Private Const BAR_NAME As String = "TolStack"

Public Sub LaunchTolStack()
    Dim launcher As String
    launcher = SCRIPT_DIR & "\TolStack_Launcher.pyw"
    ' pyw = windowless Python launcher (installed with python.org Python).
    Shell "pyw """ & launcher & """", vbNormalFocus
End Sub

Public Sub AddTolStackButton()
    RemoveTolStackButton
    On Error Resume Next
    Dim bar As CommandBar, btn As CommandBarButton
    Set bar = Application.CommandBars.Add(Name:=BAR_NAME, Position:=msoBarFloating, Temporary:=True)
    Set btn = bar.Controls.Add(Type:=msoControlButton)
    btn.Caption = "Open TolStack"
    btn.Style = msoButtonCaption
    btn.OnAction = "LaunchTolStack"
    btn.Tag = "TolStackLaunch"
    bar.Width = 120
    bar.Visible = True
    On Error GoTo 0
End Sub

Public Sub RemoveTolStackButton()
    On Error Resume Next
    Application.CommandBars(BAR_NAME).Delete
    On Error GoTo 0
End Sub
