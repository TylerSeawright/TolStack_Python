# Install-TolStack-AddIn.ps1
# One-time installer. Builds a small TolStack add-in (.xlam) that, every Excel
# session, shows an "Open TolStack" button on the Add-Ins ribbon tab. The button
# launches the always-on-top TolStack app (which pip-installs missing Python
# packages on first run). The add-in recreates its own button cleanly on open,
# so there is never a stale/broken toolbar.
#
# (Note: a true Quick Access Toolbar button is not possible from an add-in --
#  Excel does not expose .xlam macros to the QAT -- so the button lives on the
#  Add-Ins tab, which is the reliable placement in current Excel.)
#
# Run:  right-click -> "Run with PowerShell"
#       or:  powershell -ExecutionPolicy Bypass -File Install-TolStack-AddIn.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "TolStack add-in installer"
Write-Host "Project: $scriptDir"
$xlam = Join-Path (Join-Path $env:APPDATA "Microsoft\AddIns") "TolStack.xlam"

# 1) Trust access to the VBA project object model (needed to inject VBA).
foreach ($ver in @("16.0","15.0","14.0")) {
    $base = "HKCU:\Software\Microsoft\Office\$ver\Excel"
    if (Test-Path $base) {
        $sec = Join-Path $base "Security"
        if (-not (Test-Path $sec)) { New-Item -Path $sec -Force | Out-Null }
        Set-ItemProperty -Path $sec -Name "AccessVBOM" -Value 1 -Type DWord
    }
}

# 2) Clean up prior registrations so we start fresh.
foreach ($ver in @("16.0","15.0","14.0")) {
    $opt = "HKCU:\Software\Microsoft\Office\$ver\Excel\Options"
    if (Test-Path $opt) {
        foreach ($p in (Get-Item $opt).Property) {
            if ($p -like "OPEN*") {
                $val = (Get-ItemProperty -Path $opt -Name $p).$p
                if ($val -like "*TolStack*") { Remove-ItemProperty -Path $opt -Name $p }
            }
        }
    }
}
if (Test-Path $xlam) { try { Remove-Item $xlam -Force } catch {} }

# 3) VBA. The add-in creates its own "Open TolStack" button on open, bound to a
#    macro that exists in THIS same file, so the binding always resolves.
$modCode = @"
Public Const SCRIPT_DIR As String = "$scriptDir"
Private Const BAR_NAME As String = "TolStack"

Public Sub LaunchTolStack()
    On Error Resume Next
    ' pyw = windowless Python launcher (installed with python.org Python).
    Shell "pyw """ & SCRIPT_DIR & "\TolStack_Launcher.pyw""", vbNormalFocus
    On Error GoTo 0
End Sub

Public Sub RemoveStaleBars()
    On Error Resume Next
    Application.CommandBars(BAR_NAME).Delete
    On Error GoTo 0
End Sub

Public Sub AddTolStackBar()
    RemoveStaleBars
    On Error Resume Next
    Dim bar As CommandBar, btn As CommandBarButton
    Set bar = Application.CommandBars.Add(Name:=BAR_NAME, Position:=msoBarFloating, Temporary:=True)
    Set btn = bar.Controls.Add(Type:=msoControlButton)
    btn.Caption = "Open TolStack"
    btn.Style = msoButtonCaption
    btn.OnAction = "'" & ThisWorkbook.Name & "'!LaunchTolStack"
    bar.Width = 120
    bar.Visible = True
    On Error GoTo 0
End Sub
"@
$thisWb = @"
Private Sub Workbook_Open()
    AddTolStackBar
End Sub
Private Sub Workbook_BeforeClose(Cancel As Boolean)
    RemoveStaleBars
End Sub
"@

# 4) Build + register the add-in.
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $addinsDir = Split-Path $xlam
    if (-not (Test-Path $addinsDir)) { New-Item -ItemType Directory -Path $addinsDir | Out-Null }
    $wb = $excel.Workbooks.Add()
    try { $proj = $wb.VBProject } catch {
        throw "Could not access the VBA project. In Excel: File > Options > Trust Center > Trust Center Settings > Macro Settings > tick 'Trust access to the VBA project object model', then re-run."
    }
    $mod = $proj.VBComponents.Add(1)   # 1 = vbext_ct_StdModule
    $mod.Name = "TolStackMod"
    $mod.CodeModule.AddFromString($modCode)
    $proj.VBComponents("ThisWorkbook").CodeModule.AddFromString($thisWb)
    $wb.SaveAs($xlam, 55)   # 55 = xlOpenXMLAddIn (.xlam)
    $wb.Close($false)

    $tmp = $excel.Workbooks.Add()
    try { $addin = $excel.AddIns.Add($xlam, $false); $addin.Installed = $true }
    catch {
        $opt = "HKCU:\Software\Microsoft\Office\16.0\Excel\Options"
        if (-not (Test-Path $opt)) { New-Item -Path $opt -Force | Out-Null }
        $slot = 0
        while (Get-ItemProperty -Path $opt -Name ("OPEN" + $(if($slot){$slot})) -ErrorAction SilentlyContinue) { $slot++ }
        Set-ItemProperty -Path $opt -Name ("OPEN" + $(if($slot){$slot})) -Value ('/R "' + $xlam + '"') -Type String
    }
    $tmp.Close($false)
}
finally {
    $excel.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    Start-Sleep -Seconds 2
}

Write-Host "Installed add-in: $xlam"
Write-Host "Done. Close and reopen Excel - click the Add-Ins tab, then 'Open TolStack'."
