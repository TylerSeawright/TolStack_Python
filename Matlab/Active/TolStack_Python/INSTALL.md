# TolStack — install & launch

The app is an always-on-top floating panel (Check Path, Solve, Export Data,
New Template, Pin-on-top) that reads your highlighted Excel range. On first run
it pip-installs any missing Python packages.

## Reliable launcher (recommended)

1. Make sure **Python** is installed (python.org — provides the `pyw` launcher).
2. Double-click **`Create_Desktop_Shortcut.bat`** once. It puts a **TolStack**
   shortcut on your Desktop.
3. Double-click that shortcut any time to open the panel. (First launch installs
   `numpy`, `matplotlib`, `openpyxl`, `pywin32` automatically.)

That's it — highlight your input range in Excel, then use the panel's buttons.

## Optional: a button inside Excel

`Install-TolStack-AddIn.ps1` installs a `TolStack.xlam` add-in that adds an
**Open TolStack** button to the **Add-Ins ribbon tab** (Excel does not allow
add-in macros on the Quick Access Toolbar, so the Add-Ins tab is the placement).

- Right-click `Install-TolStack-AddIn.ps1` → **Run with PowerShell**, then close
  and reopen Excel. Click the **Add-Ins** tab → **Open TolStack**.
- On some Excel builds the button may not render (macro-trust / add-in-loading
  behavior varies by installation). If it doesn't appear, just use the desktop
  shortcut above — it runs the identical app.

To remove the add-in later: File → Options → Add-ins → Manage: Excel Add-ins →
Go… → untick **TolStack**.

## Notes

- The panel floats on top of Excel (untick **Pin on top** for normal behavior).
- If Excel shows **Protected View**, click *Enable Editing* before Solve — the
  backend can't read a protected workbook.
