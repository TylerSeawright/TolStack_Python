"""
excel_io.py
Read from / write to the LIVE running Excel application (Windows COM).

Direct port of the MATLAB functions:
    ReadActiveExcel.m  -> read_active_excel()
    write_results.m    -> write_results()

Requires Windows with Excel installed and pywin32 (`pip install pywin32`).
The workbook must already be open; for reading, the desired range must be
highlighted (selected) in Excel exactly as in the MATLAB workflow.
"""

from __future__ import annotations

from typing import List, Tuple


def _get_running_excel():
    """Attach to the already-running Excel instance (like actxGetRunningServer)."""
    try:
        import win32com.client
    except ImportError as exc:  # pragma: no cover - platform dependent
        raise RuntimeError(
            "pywin32 is required for live Excel access. Install with:\n"
            "    pip install pywin32"
        ) from exc

    try:
        # GetActiveObject attaches to an existing Excel.Application instance.
        excel = win32com.client.GetActiveObject("Excel.Application")
    except Exception as exc:  # pragma: no cover - platform dependent
        raise RuntimeError(
            "Could not find a running Excel instance. Open your workbook in "
            "Excel first, then try again."
        ) from exc
    return excel


def _to_str(value) -> str:
    """Convert a cell value to a string the way MATLAB `string()` would,
    turning empty/missing cells into the token 'NaN' (matches fillmissing)."""
    if value is None:
        return "NaN"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        # Render whole-number floats without a trailing .0 so tags/text match,
        # but keep precision for real decimals.
        if value.is_integer():
            return str(int(value))
        return repr(value)
    return str(value)


def read_active_excel() -> Tuple[List[List[str]], str, Tuple[int, int]]:
    """Read the currently selected range from the active Excel window.

    Returns
    -------
    data : list[list[str]]
        2-D grid of the selection as strings (missing -> "NaN").
    address : str
        The selection address (e.g. '$B$8:$H$11').
    startcell : (row, col)
        Absolute 1-based (row, column) of the selection's top-left cell.
    """
    excel = _get_running_excel()
    excel.Visible = True

    selection = excel.Selection
    address = str(selection.Address)

    first_cell = selection.Cells(1)
    start_row = int(first_cell.Row)
    start_col = int(first_cell.Column)

    raw = selection.Value  # scalar, 1-D tuple, or 2-D tuple-of-tuples

    # Normalize into a 2-D list of strings.
    if raw is None:
        data = [["NaN"]]
    elif not isinstance(raw, tuple):
        data = [[_to_str(raw)]]
    elif len(raw) > 0 and isinstance(raw[0], tuple):
        data = [[_to_str(v) for v in row] for row in raw]
    else:
        # Single row returned as a flat tuple.
        data = [[_to_str(v) for v in raw]]

    return data, address, (start_row, start_col)


def write_results(result_cell: Tuple[int, int], data) -> None:
    """Write 6 result values into the 6 cells to the RIGHT of RESULT cell.

    Mirrors MATLAB write_results.m: writes to Cells(row, col + j) for j = 1..6
    on the active sheet of the first open workbook, then saves.
    """
    excel = _get_running_excel()
    excel.Visible = True

    workbook = excel.Workbooks(1)  # assume the target workbook is the first open
    sheet = workbook.ActiveSheet

    row = int(result_cell[0])
    col = int(result_cell[1])
    for j in range(1, 7):
        sheet.Cells(row, col + j).Value = float(data[j - 1])

    workbook.Save()
