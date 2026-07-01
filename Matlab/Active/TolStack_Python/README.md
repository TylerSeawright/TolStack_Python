# TolStack — Python Edition

A Python port of the MATLAB App Designer tool `TolStack.mlapp`. It runs a
Monte-Carlo tolerance-stack (error-budget) simulation that propagates 6-DOF
error through a chain of homogeneous transformation matrices (HTMs), reading
its inputs from the **live, currently-selected range in Excel** — exactly like
the original MATLAB app.

## How it works

The GUI is a small Tkinter window with two buttons, mirroring the `.mlapp`:

- **Solve** — reads the highlighted Excel range, runs the Monte-Carlo
  simulation, optionally shows plots, and writes `mu + N*sigma` back into the
  six cells to the right of the `RESULT` tag.
- **Check Path** — reads the range and plots the nominal coordinate-system path
  (CS0, CS1, CS2, …) so you can visually confirm the vector chain.

Just like the MATLAB version, you first open your workbook in Excel, highlight
the block of cells containing the tagged inputs, then click a button.

## Input format (unchanged from the MATLAB app)

Inside your highlighted selection, the parser looks for these tags. Each tag
sits in a cell, and its values are read from the cells immediately to the right:

| Tag            | Values read | Meaning                                   |
|----------------|-------------|-------------------------------------------|
| `R`            | 6           | Nominal vector (X Y Z Tx Ty Tz); one row per segment |
| `Re`           | 6           | Random error terms (N-sigma), one row per `R` |
| `C`            | 6           | Compensator (optional)                    |
| `Cv`           | 6           | Compensator vector (optional)             |
| `N_SAMPLES`    | 1           | Monte-Carlo sample count (default 1000)   |
| `N_SIGMA`      | 1           | Sigma multiplier (default 3)              |
| `RESULT`       | —           | Anchor cell; results written to its right |
| `PLOT`         | 1           | 1 = generate plots, 0 = none              |
| `NAME`         | 1           | Stack name (text)                         |
| `DISTRIBUTION` | 1           | Input distribution label (Normal)         |

`R` and `Re` are required. Angles are in radians, positions in the sheet's units.

## Install & run (Windows)

```
pip install -r requirements.txt
python app.py
```

- **Windows + Microsoft Excel is required** for the live-Excel reading and
  write-back (via `pywin32` COM automation), matching the original
  `actxGetRunningServer('Excel.Application')` behavior.
- Open your workbook, highlight the input range, then click **Solve** or
  **Check Path**.

## File map (MATLAB → Python)

| Python module   | Ported MATLAB source                                             |
|-----------------|-----------------------------------------------------------------|
| `transforms.py` | `Tform.m`, `CoordTform.m`, `extract_HTM_error.m`, `data_transform.m`, `COORD.m`, `comp.m` |
| `excel_io.py`   | `ReadActiveExcel.m`, `write_results.m`                           |
| `solver.py`     | `STACKRANGE.m`, `tag_parse.m`, `fetchstack.m`, `check_inputs.m`, `nrd.m`, `solve_error_comp.m`, `err_correct2.m`, `TolStackSolve.m` |
| `plotting.py`   | `plot_histogram.m`, `plot_coord2.m`                             |
| `app.py`        | `TolStack.mlapp` (the App Designer GUI + `TolStack_Button.m`)   |

## Notes on fidelity

- Rotation order is preserved: 3-2-1 (`Rz*Ry*Rx*Translate` for `"o"`,
  `Translate*Rz*Ry*Rx` for `"p"`).
- `extract_HTM_error` uses the **exact same formula** as the MATLAB original
  (a small-angle approximation for the Z rotation), so results match the
  MATLAB tool rather than a "corrected" decomposition.
- Sample standard deviation uses `ddof=1`, matching MATLAB's default `std`.
- The compensation branch triggers on the same condition as MATLAB
  (`~all(C)`), and an all-zero compensator leaves the error unchanged.

## Building a standalone .exe (no Python needed by end users)

The repo includes a PyInstaller spec and a one-click build script. On a Windows
machine that has Python installed:

```
cd TolStack_Python
build.bat
```

This installs the dependencies (numpy, matplotlib, pywin32, pyinstaller) and
produces a single windowed executable at:

```
TolStack_Python\dist\TolStack.exe
```

Copy `TolStack.exe` anywhere and double-click to launch — no Python install is
required on the target machine. It still needs Microsoft Excel to be running
with the workbook open and the input range highlighted, exactly like the
script and the original MATLAB app.

Notes:
- The window/taskbar icon and exe icon come from `TolStack.ico` (generated from
  `TolStackIcon2.png`).
- `build.bat` uses `TolStack.spec`; edit the spec if you want a folder build
  (`console=False`, `--onedir`) instead of the default single-file build.
