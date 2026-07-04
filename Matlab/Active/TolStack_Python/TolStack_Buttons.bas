Attribute VB_Name = "TolStack"
' TolStack on-sheet button macros.
' Each button just launches the headless Python backend, which attaches to THIS
' running Excel instance, reads the highlighted selection, writes the results,
' and embeds/replaces the plots on the sheet.
'
' Setup: assign TolStack_Solve to the "Solve" button and TolStack_CheckPath to
' the "Check Path" button. Adjust SCRIPT_DIR below if you move the project.

Private Const SCRIPT_DIR As String = _
    "C:\Users\tyman\OneDrive\Documents\GitHub\TolStack\Matlab\Active\TolStack_Python"

Private Sub RunTolStack(mode As String)
    Dim script As String, cmd As String
    script = SCRIPT_DIR & "\tolstack_cli.py"
    ' pyw = windowless Python launcher (installed with python.org Python).
    cmd = "pyw """ & script & """ " & mode
    On Error Resume Next
    ActiveWorkbook.Save                 ' persist edits before the backend reads
    On Error GoTo 0
    Shell cmd, vbNormalFocus
End Sub

Public Sub TolStack_Solve()
    RunTolStack "solve"
End Sub

Public Sub TolStack_CheckPath()
    RunTolStack "checkpath"
End Sub
