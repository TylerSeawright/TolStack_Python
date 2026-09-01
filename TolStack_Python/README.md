# TolStack — Python Edition

A Monte-Carlo tolerance-stack (error-budget) tool that propagates 6-DOF error
through a chain of homogeneous transformation matrices (HTMs). Excel is the
front end: you lay out the stack in cells, highlight the range, and run — results
and plots are written straight back into the sheet.

Python port of the MATLAB App Designer tool `TolStack.mlapp`, hardened and
extended for open-source use. See `MATH_VERIFICATION.md` for the numerical
verification report.

## What's new vs. the original

- **Exact rotation extraction** (`eps_z`) — no more small-angle drift.
- **Hardened input validation** — blank/NaN cells, `N_SAMPLES<2`, `N_SIGMA<=0`
  are reported instead of silently producing `NaN`.
- **Vectorized Monte-Carlo** — ~100–250× faster (batched 4×4 ops).
- **Input distributions** — Normal, Uniform, or Triangular (per the
  `DISTRIBUTION` tag), plus optional correlation in the API.
- **Reproducible runs** — optional `SEED`.
- **Stochastic compensator** — a new `Ce` term gives the corrector its own
  zero-mean repeatability error (imperfect adjustment), propagated with the same
  coupling as the correction itself.
- **Richer outputs** — `MU`, `SIGMA`, `RESULT` (μ+Nσ) and `WORST_CASE`
  (|μ|+Nσ), plus Monte-Carlo standard error / 95% CI available in the API.
- **Sensitivity / tornado** — variance contribution of each error source.
- **Plots embedded in Excel** — histograms, coordinate path, and tornado are
  inserted into the sheet and **replaced** on each re-run.
- **Cross-platform file mode** — run headless from an `.xlsx` with no Excel
  (used by the test suite / CI).
- **Tests + CI + MIT license.**

## Input tags

Put each tag in a cell; its values are read from the cells immediately to the
right. Highlight the block containing them, then Solve.

| Tag | Values | Meaning |
|-----|--------|---------|
| `R` | 6 | Nominal vector `X Y Z Tx Ty Tz` (one row per segment) |
| `Re` | 6 | Random error (± value at `N_SIGMA`), one row per `R` |
| `C` | 6 | Compensator setpoint (nonzero = active DOF) |
| `Cv` | 6 | Compensator lever vector (offset to the corrector) |
| `Ce` | 6 | **Compensator error** — zero-mean corrector repeatability (± at `N_SIGMA`) |
| `N_SAMPLES` | 1 | Monte-Carlo trials (≥2, default 1000) |
| `N_SIGMA` | 1 | Sigma multiplier the tolerances are quoted at (default 3) |
| `DISTRIBUTION` | 1 | `N` Normal, `U` Uniform, `T` Triangular |
| `SEED` | 1 | Optional RNG seed. **Blank = a new random draw each run** (a Monte-Carlo should vary); a number = reproducible identical results |
| `PLOT` | 1 | `1` embed plots in the sheet, `0` none |
| `SHOW` | 1 | `1` also open interactive, rotatable plot windows (not captured by the embedded PNG) |
| `NAME` | 1 | Stack name (plot titles) |
| `RESULT` | — | Anchor; μ+Nσ written to its right |
| `MU` / `SIGMA` / `WORST_CASE` | — | Optional anchors for mean, 1σ, and |μ|+Nσ |

Angles are radians, positions in the sheet's units. `R` and `Re` are required.

## Excel-native buttons (the whole UI is Excel)

`TolStack_Template.xlsx` has a ready-made example tab. To add the two on-sheet
buttons once (no Developer tab needed):

1. Open the template and **Save As → `TolStack_Template.xlsm`** (Excel
   Macro-Enabled Workbook).
2. **Alt+F11** → in the editor, `Insert → Module`, and paste the contents of
   **`TolStack_Buttons.bas`** (edit `SCRIPT_DIR` if you move the project).
   Close the editor.
3. On the sheet, `Insert → Shapes` → draw a rounded rectangle, type "Solve".
   Right-click it → **Assign Macro** → `TolStack_Solve`.
4. Draw a second shape "Check Path", Assign Macro → `TolStack_CheckPath`.

Now the workflow is entirely in Excel: highlight the input range and click
**Solve** (writes results + embeds plots) or **Check Path** (embeds the nominal
path plot). The buttons launch the Python backend, which attaches to the open
workbook via COM. A fallback mini-window (`TolStack_Dev.bat` / desktop shortcut)
runs the identical backend if you prefer, and adds an **Export Data** button
that saves the raw Monte-Carlo histogram samples to `.csv` or `.xlsx`.

Embedded plots are laid out left-to-right: the **coordinate path** first, the
**error histogram** to its right, then the **sensitivity tornado**. Re-running
Solve replaces them. The template's first tab is a full **Instructions** sheet.

> Requires Windows + Excel for the live/button workflow (via `pywin32`). Make
> sure the workbook is **not** in Protected View (click *Enable Editing*).

## Install & run

```
pip install -r requirements.txt
```

- Buttons / mini-window: highlight the range, click Solve.
- Headless (any OS, no Excel — used by CI):
  ```
  python tolstack_cli.py solve --file TolStack_Template.xlsx --sheet Example
  ```

## Tests

```
python build_template.py      # generates the example workbook the IO test uses
pytest -q
```
CI runs the suite on Python 3.10–3.12 (`.github/workflows/ci.yml`).

## File map

| Module | Role |
|--------|------|
| `transforms.py` | HTM math (scalar + batched); exact & log-map extraction |
| `solver.py` | parsing, validation, distributions, vectorized MC, compensator, sensitivity |
| `excel_io.py` | live Excel via COM (same-workbook read/write, plot embedding) |
| `file_io.py` | openpyxl backend (headless / cross-platform / CI) |
| `plotting.py` | histograms, coordinate path, tornado |
| `tolstack_cli.py` | headless entry point the buttons call (`solve` / `checkpath`) |
| `app.py` | optional Tkinter fallback window |
| `TolStack_Buttons.bas` | VBA for the on-sheet buttons |
| `tests/` | pytest suite |

## Notes on fidelity

- Rotation order 3-2-1 (`Rz*Ry*Rx*Translate` for `"o"`).
- `extract_HTM_error` recovers ZYX angles exactly; `rotation_vector_error`
  offers an order-independent, gimbal-lock-free alternative.
- Sample std uses `ddof=1` (matches MATLAB `std`).
- **Normal** sampling is bit-identical to the original tool, so existing Normal
  workbooks are unchanged.
- The MATLAB sources under `Matlab/Active/` were updated in parallel to keep the
  `.m` reference in sync (exact `eps_z`, gate, guards, distributions, `Ce`).
