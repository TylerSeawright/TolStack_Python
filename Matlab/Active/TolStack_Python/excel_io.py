"""excel_io.py — live Excel via Windows COM (pywin32).

Used by the on-sheet buttons so the ALREADY-OPEN workbook is edited in place
(read the highlighted selection, write results, embed/replace plot images).
Cross-platform / headless runs use file_io.py instead.
"""
from __future__ import annotations
import os
from typing import List, Tuple

_SHAPE_PREFIX = "TolStackPlot_"   # our images are named with this prefix


class ExcelError(RuntimeError):
    pass


def _to_str(value) -> str:
    if value is None: return "NaN"
    if isinstance(value, bool): return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else repr(value)
    return str(value)


def get_running_excel():
    try:
        import win32com.client
    except ImportError as e:
        raise ExcelError("pywin32 is required for live Excel. pip install pywin32") from e
    try:
        return win32com.client.GetActiveObject("Excel.Application")
    except Exception as e:
        raise ExcelError("No running Excel instance found. Open your workbook first.") from e


class ExcelSession:
    """Binds to the workbook/sheet that owns the current selection, so reads
    and writes always target the same place (fixes the Workbooks(1) bug)."""
    def __init__(self):
        self.excel = get_running_excel()
        self.excel.Visible = True
        sel = self.excel.Selection
        if sel is None:
            raise ExcelError("Nothing is selected in Excel.")
        self.selection = sel
        self.sheet = sel.Worksheet
        self.workbook = self.sheet.Parent

    # ---- read ----
    def read_selection(self) -> Tuple[List[List[str]], str, Tuple[int, int]]:
        sel = self.selection
        address = str(sel.Address)
        first = sel.Cells(1, 1)
        start = (int(first.Row), int(first.Column))
        raw = sel.Value
        if raw is None:
            data = [["NaN"]]
        elif not isinstance(raw, tuple):
            data = [[_to_str(raw)]]
        elif len(raw) > 0 and isinstance(raw[0], tuple):
            data = [[_to_str(v) for v in row] for row in raw]
        else:
            data = [[_to_str(v) for v in raw]]
        return data, address, start

    # ---- write ----
    def write_vector(self, cell: Tuple[int, int], values) -> None:
        r, c = int(cell[0]), int(cell[1])
        for j in range(1, 7):
            self.sheet.Cells(r, c + j).Value = float(values[j - 1])

    def write_results(self, result_cells: dict, vectors: dict) -> None:
        for tag, cell in result_cells.items():
            vec = vectors.get(tag)
            if vec is not None:
                self.write_vector(cell, vec)

    # ---- images (replace on re-run) ----
    def clear_plots(self) -> None:
        # iterate a snapshot because deleting mutates the Shapes collection
        for shp in list(self.sheet.Shapes):
            try:
                if str(shp.Name).startswith(_SHAPE_PREFIX):
                    shp.Delete()
            except Exception:
                pass

    def embed_images(self, image_paths: List[str], anchor_cell=(2, 11),
                     gap_px=20) -> None:
        """Insert PNGs left-to-right (path plot first, output histogram to its
        right, tornado next), deleting any previous TolStack images first so a
        re-run replaces them. anchor_cell is (row, col) top-left."""
        self.clear_plots()
        rng = self.sheet.Cells(int(anchor_cell[0]), int(anchor_cell[1]))
        top = float(rng.Top); x = float(rng.Left)
        for i, p in enumerate(image_paths):
            pic = self.sheet.Shapes.AddPicture(str(p), False, True, x, top, -1, -1)
            pic.Name = f"{_SHAPE_PREFIX}{i}"
            x += pic.Width + gap_px

    def save(self) -> None:
        try:
            self.workbook.Save()
        except Exception:
            pass


# ---- backward-compatible module-level helpers (used by older code paths) ----
def read_active_excel():
    return ExcelSession().read_selection()


def write_results(result_cell, data):
    s = ExcelSession()
    s.write_vector(result_cell, data)
    s.save()


# Section fill colors as (R, G, B).
_C_SECTION = (142, 170, 219)
_C_HEADER = (48, 84, 150)
_C_GREEN = (198, 239, 206)
_C_RED = (255, 199, 206)
_C_BLUE = (189, 215, 238)
_C_GOLD = (255, 230, 153)
_C_PURPLE = (228, 223, 236)


def _rgb(c):
    """Excel Interior.Color wants a BGR long."""
    r, g, b = c
    return r + (g << 8) + (b << 16)


# Template layout: (kind, *args). Mirrors the Example tab in build_template.py.
_TEMPLATE = [
    ("title", "TolStack — Example Stack"),
    ("note", "Fill the colored cells, highlight this block (A4:I32), then Solve."),
    ("blank",),
    ("section", "NOMINAL VECTOR PATH  (positions mm, angles rad)"),
    ("colhdr",),
    ("row", _C_GREEN, "R1", "R", [10, 0, 0, 0, 0, 0], "10 mm along X"),
    ("row", _C_GREEN, "R2", "R", [0, 10, 0, 0, 0, 0], "10 mm along Y"),
    ("row", _C_GREEN, "R3", "R", [0, 0, 5, 0, 0, 0], "5 mm along Z"),
    ("section", "RANDOM ERROR TERMS  (± value at N_SIGMA)"),
    ("colhdr",),
    ("row", _C_RED, "R1e", "Re", [0.02, 0.02, 0, 0, 0, 0.001], "pos/ang tol at joint 1"),
    ("row", _C_RED, "R2e", "Re", [0.02, 0.02, 0, 0, 0, 0], ""),
    ("row", _C_RED, "R3e", "Re", [0, 0, 0.03, 0.0005, 0.0005, 0], ""),
    ("section", "COMPENSATOR  (C=setpoint, Cv=lever, Ce=repeatability ±@Nσ)"),
    ("colhdr",),
    ("row", _C_BLUE, "C1", "C", [0, 0, 0, 0, 0, 0.0005], "nulls Tz toward setpoint"),
    ("row", _C_BLUE, "C1v", "Cv", [10, 0, 0, 0, 0, 0], "corrector 10 mm away"),
    ("row", _C_BLUE, "C1e", "Ce", [0, 0, 0, 0, 0, 0.0002], "corrector zero-mean error"),
    ("section", "MONTECARLO CONFIG"),
    ("cfg", "MC Samples", "N_SAMPLES", 10000, "# of trials (>=2)"),
    ("cfg", "Sigma", "N_SIGMA", 3, "tolerance is at this many sigma"),
    ("cfg", "Distribution", "DISTRIBUTION", "N", "N=Normal, U=Uniform, T=Triangular"),
    ("cfg", "Seed", "SEED", None, "blank = new random draw each run; a number = reproducible"),
    ("cfg", "Make Plots", "PLOT", 1, "1=embed plots in sheet, 0=none"),
    ("cfg", "Open Plot Windows", "SHOW", 0, "1=also open interactive (rotatable) windows"),
    ("cfg", "Stack Name", "NAME", "Example", "label for plots"),
    ("section", "SIMULATION RESULTS  (written by Solve)"),
    ("colhdr",),
    ("res", "mu + Nσ (spec)", "RESULT", "upper estimate mean+Nσ"),
    ("res", "Mean", "MU", "systematic bias"),
    ("res", "Sigma (1σ)", "SIGMA", "random spread"),
    ("res", "|mu| + Nσ (worst)", "WORST_CASE", "conservative worst case"),
]


def _fill_row(ws, r, color):
    ws.Range(ws.Cells(r, 1), ws.Cells(r, 9)).Interior.Color = _rgb(color)


def insert_template_tab(source_sheet="Example"):
    """Add a fresh TolStack template as a NEW SHEET in the ACTIVE workbook (never a
    new workbook). Does not touch the user's existing sheets. Returns the tab name."""
    excel = get_running_excel()
    excel.Visible = True
    active = excel.ActiveWorkbook
    if active is None:
        active = excel.Workbooks.Add()   # nothing open -> give them a workbook

    # Unique sheet name.
    existing = {active.Sheets(k).Name for k in range(1, active.Sheets.Count + 1)}
    base = "TolStack"; name = base; i = 1
    while name in existing:
        i += 1; name = f"{base}{i}"

    # New sheet at the end of THIS workbook.
    ws = active.Worksheets.Add(After=active.Sheets(active.Sheets.Count))
    ws.Name = name

    hdr = ["Vector Name", "Vector Tag", "X", "Y", "Z", "Tx", "Ty", "Tz", "Notes"]
    r = 1
    for entry in _TEMPLATE:
        kind = entry[0]
        if kind == "title":
            ws.Cells(r, 1).Value = entry[1]; ws.Cells(r, 1).Font.Size = 15
            ws.Cells(r, 1).Font.Bold = True
        elif kind == "note":
            ws.Cells(r, 1).Value = entry[1]; ws.Cells(r, 1).Font.Italic = True
        elif kind == "blank":
            pass
        elif kind == "section":
            ws.Cells(r, 1).Value = entry[1]
            _fill_row(ws, r, _C_SECTION)
            ws.Range(ws.Cells(r, 1), ws.Cells(r, 9)).Font.Bold = True
        elif kind == "colhdr":
            for j, h in enumerate(hdr): ws.Cells(r, 1 + j).Value = h
            _fill_row(ws, r, _C_HEADER)
            rng = ws.Range(ws.Cells(r, 1), ws.Cells(r, 9))
            rng.Font.Bold = True; rng.Font.Color = _rgb((255, 255, 255))
        elif kind == "row":
            _, color, nm, tag, vals, note = entry
            ws.Cells(r, 1).Value = nm; ws.Cells(r, 2).Value = tag
            for j, v in enumerate(vals): ws.Cells(r, 3 + j).Value = v
            if note: ws.Cells(r, 9).Value = note
            _fill_row(ws, r, color)
        elif kind == "cfg":
            _, nm, tag, val, note = entry
            ws.Cells(r, 1).Value = nm; ws.Cells(r, 2).Value = tag
            if val is not None: ws.Cells(r, 3).Value = val
            ws.Cells(r, 9).Value = note
            _fill_row(ws, r, _C_GOLD)
        elif kind == "res":
            _, nm, tag, note = entry
            ws.Cells(r, 1).Value = nm; ws.Cells(r, 2).Value = tag
            ws.Cells(r, 9).Value = note
            _fill_row(ws, r, _C_PURPLE)
        r += 1

    # Column widths.
    for col, w in ((1, 18), (2, 13), (3, 9), (4, 9), (5, 9), (6, 9), (7, 9), (8, 9), (9, 34)):
        ws.Columns(col).ColumnWidth = w
    ws.Activate()
    return name
