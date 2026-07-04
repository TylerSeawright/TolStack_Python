"""tolstack_cli.py — headless entry point driven by the on-sheet Excel buttons.

Live Excel (what the buttons call):
    pythonw tolstack_cli.py solve
    pythonw tolstack_cli.py checkpath
Headless / cross-platform (batch, CI):
    python tolstack_cli.py solve --file book.xlsx --sheet Example
Export the raw Monte-Carlo histogram data:
    python tolstack_cli.py export --file book.xlsx --sheet Example --out data.csv
"""
from __future__ import annotations
import argparse, csv, os, sys, tempfile, traceback
import matplotlib   # backend chosen lazily (Agg by default, TkAgg if SHOW=1)

from solver import (StackRange, fetchstack, run_solve, check_inputs,
                    solve_error_comp, sensitivity_analysis)
from transforms import COORD


def _popup(title, msg):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, str(msg), str(title), 0x40)
    except Exception:
        sys.stderr.write(f"{title}: {msg}\n")


def _set_backend(show):
    """Pick the matplotlib backend BEFORE pyplot is imported. Interactive
    (TkAgg) when the user wants rotatable windows, else headless Agg."""
    try:
        matplotlib.use("TkAgg" if show else "Agg", force=True)
    except Exception:
        matplotlib.use("Agg", force=True)


def _make_plots(s, outdir, want=("coord", "hist", "tornado"), keep=False):
    """Render plots to PNGs. Returns (paths, figs). PNG order is path-first so
    the embed places the output histogram to the RIGHT of the path plot."""
    import matplotlib.pyplot as plt
    import plotting
    paths, figs = [], []
    if "coord" in want and s.Tn_list is not None:
        f = plotting.plot_coord2(COORD(), s.Tn_list, s.Name)
        p = os.path.join(outdir, "tolstack_path.png"); f.savefig(p, dpi=110)
        paths.append(p); figs.append(f)
    if "hist" in want and getattr(s, "Error", None) is not None:
        f = plotting.plot_histogram(s.Error, s.mu, s.Nsig * s.sigma, s.Name, s.Nsig)
        p = os.path.join(outdir, "tolstack_hist.png"); f.savefig(p, dpi=110)
        paths.append(p); figs.append(f)
    if "tornado" in want:
        try:
            f = plotting.plot_tornado(sensitivity_analysis(s), s.Name, "magnitude")
            p = os.path.join(outdir, "tolstack_tornado.png"); f.savefig(p, dpi=110)
            paths.append(p); figs.append(f)
        except Exception:
            pass
    if not keep:
        for f in figs: plt.close(f)
    return paths, figs


def _result_vectors(s):
    return {"RESULT": s.uplusNsigma, "MU": s.mu, "SIGMA": s.sigma, "WORST_CASE": s.worst_case}


def export_histogram(s, path):
    """Write the raw N×6 Monte-Carlo error samples (+ summary) to .csv or .xlsx."""
    import numpy as np
    hdr = ["X", "Y", "Z", "TX", "TY", "TZ"]
    E = np.asarray(s.Error, float)
    if str(path).lower().endswith(".xlsx"):
        import openpyxl
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Histogram Data"
        ws.append(hdr)
        for row in E: ws.append([float(v) for v in row])
        sm = wb.create_sheet("Summary"); sm.append(["stat"] + hdr)
        for name, vec in (("mean", s.mu), ("sigma", s.sigma),
                          ("mu+Nsig", s.uplusNsigma), ("|mu|+Nsig", s.worst_case)):
            sm.append([name] + [float(v) for v in vec])
        wb.save(path)
    else:
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(hdr)
            for row in E: w.writerow([float(v) for v in row])
    return path


# --------------------------------------------------------------------------
def _solve_live_stackrange(seed=None):
    """Attach to Excel, read the selection, run the solve. Returns (s, session)."""
    from excel_io import ExcelSession
    sess = ExcelSession()
    data, _addr, start = sess.read_selection()
    s = fetchstack(StackRange(), data=data, startcell=start)
    if seed is not None: s.Seed = seed
    return s, sess


def run_live(mode, seed=None):
    from excel_io import ExcelError
    try:
        s, sess = _solve_live_stackrange(seed)
    except ExcelError as e:
        _popup("TolStack", f"{e}\n\nOpen the workbook, click 'Enable Editing' if it "
               "is in Protected View, then highlight the input range and try again.")
        return 1

    if mode == "checkpath":
        import numpy as np
        s = check_inputs(s)
        if s.R is None:
            _popup("TolStack", "No R vectors found in the selection."); return 1
        _, _, _, _, _, s.Tn_list, _ = solve_error_comp(
            s.R, np.zeros_like(np.atleast_2d(s.R)), s.C, s.Cv)
        _set_backend(s.Show)
        outdir = tempfile.mkdtemp(prefix="tolstack_")
        paths, figs = _make_plots(s, outdir, want=("coord",), keep=bool(s.Show))
        sess.embed_images(paths); sess.save()
        if s.Show: _show_blocking()
        return 0

    msgs = []
    s = run_solve(s, log=msgs.append)
    if s is None:
        _popup("TolStack — invalid inputs", "\n".join(msgs) or "INVALID INPUTS"); return 1
    sess.write_results(s.result_cells, _result_vectors(s))
    if s.Plot or s.Show:
        _set_backend(s.Show)
        outdir = tempfile.mkdtemp(prefix="tolstack_")
        paths, figs = _make_plots(s, outdir, keep=bool(s.Show))
        if s.Plot: sess.embed_images(paths)
    sess.save()
    if s.Show: _show_blocking()
    return 0


def _show_blocking():
    import matplotlib.pyplot as plt
    plt.show()   # keep interactive windows open for rotation/analysis


def run_file(mode, path, sheet, seed=None):
    import file_io, numpy as np
    grid, start = file_io.read_workbook(path, sheet)
    s = fetchstack(StackRange(), data=grid, startcell=start)
    if seed is not None: s.Seed = seed
    _set_backend(False)   # file mode is always headless
    if mode == "checkpath":
        s = check_inputs(s)
        _, _, _, _, _, s.Tn_list, _ = solve_error_comp(
            s.R, np.zeros_like(np.atleast_2d(s.R)), s.C, s.Cv)
        outdir = os.path.dirname(os.path.abspath(path))
        paths, _ = _make_plots(s, outdir, want=("coord",))
        file_io.embed_images(path, sheet, paths); return 0
    s = run_solve(s, log=print)
    if s is None: return 1
    file_io.write_results(path, sheet, s.result_cells, _result_vectors(s))
    if s.Plot:
        outdir = os.path.dirname(os.path.abspath(path))
        paths, _ = _make_plots(s, outdir)
        file_io.embed_images(path, sheet, paths)
    return s


def run_export(path, sheet, out, seed=None):
    import file_io
    grid, start = file_io.read_workbook(path, sheet)
    s = fetchstack(StackRange(), data=grid, startcell=start)
    if seed is not None: s.Seed = seed
    _set_backend(False)
    s = run_solve(s, log=print)
    if s is None: return 1
    export_histogram(s, out); print("wrote", out); return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="TolStack headless runner")
    ap.add_argument("mode", choices=["solve", "checkpath", "export"])
    ap.add_argument("--file"); ap.add_argument("--sheet")
    ap.add_argument("--out", help="output path for export mode (.csv/.xlsx)")
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args(argv)
    try:
        if a.mode == "export":
            return run_export(a.file, a.sheet, a.out or "tolstack_data.csv", a.seed)
        if a.file:
            r = run_file(a.mode, a.file, a.sheet, a.seed)
            return 0 if r not in (0, 1, 2) else r
        return run_live(a.mode, a.seed)
    except Exception as e:
        _popup("TolStack — error", f"{e}\n\n{traceback.format_exc()}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
