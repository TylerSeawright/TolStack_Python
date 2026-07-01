"""
app.py
TolStack - Python edition.  Tkinter GUI that replicates the MATLAB App Designer
window (TolStack.mlapp) and drives the same Monte-Carlo tolerance-stack solver
off the LIVE Excel selection.

Run:
    python app.py

Requirements: numpy, matplotlib, pywin32 (Windows + Excel for live reading).
"""

from __future__ import annotations

import os
import sys
import traceback
import webbrowser

import tkinter as tk
from tkinter import messagebox, scrolledtext

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt  # noqa: E402

from solver import StackRange, tol_stack_solve, fetchstack, solve_error_comp  # noqa: E402
from transforms import COORD  # noqa: E402
import plotting  # noqa: E402


# Original colors from the .mlapp (RGB 0-1 -> hex).
BG_COLOR = "#DBF7FF"          # [0.8588 0.9686 1]
SOLVE_COLOR = "#00FF00"       # green
CHECKPATH_COLOR = "#00FFFF"   # cyan

DOWNLOAD_URL = "https://github.com/"  # placeholder; original hyperlink text only


def _resource_dir() -> str:
    """Folder that holds bundled resources (PNG/ICO)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


RES_DIR = _resource_dir()


def _find_icon(png_names, ico_name="TolStack.ico"):
    """Return (png_path, ico_path), searching the bundle dir and MATLAB folder."""
    here = os.path.dirname(os.path.abspath(__file__))
    search = [RES_DIR, os.path.join(RES_DIR, ".."), here, os.path.join(here, "..")]
    png = ico = None
    for d in search:
        if png is None:
            for n in png_names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    png = p
                    break
        if ico is None:
            p = os.path.join(d, ico_name)
            if os.path.exists(p):
                ico = p
    return png, ico


ICON_PNG, ICON_ICO = _find_icon(["TolStackIcon3.png", "TolStackIcon2.png"])


class TolStackApp:
    def __init__(self, root):
        self.root = root
        root.title("TolStack")
        root.configure(bg=BG_COLOR)
        root.geometry("360x360")
        root.resizable(False, False)

        if ICON_ICO:
            try:
                root.iconbitmap(ICON_ICO)
            except Exception:
                pass

        header = tk.Frame(root, bg=BG_COLOR)
        header.pack(fill="x", padx=12, pady=(10, 0))

        title_col = tk.Frame(header, bg=BG_COLOR)
        title_col.pack(side="left", anchor="n")

        title_row = tk.Frame(title_col, bg=BG_COLOR)
        title_row.pack(anchor="w")
        tk.Label(title_row, text="TolStack", font=("Segoe UI", 24, "bold"),
                 bg=BG_COLOR).pack(side="left")
        tk.Label(title_row, text="V1.0", font=("Segoe UI", 10),
                 bg=BG_COLOR).pack(side="left", padx=(6, 0), pady=(14, 0))

        tk.Label(title_col, text="Created by Tyler Seawright",
                 font=("Segoe UI", 9), bg=BG_COLOR).pack(anchor="w")

        link1 = tk.Label(title_col, text="Download Latest Version Here", fg="blue",
                         cursor="hand2", bg=BG_COLOR,
                         font=("Segoe UI", 9, "underline"))
        link1.pack(anchor="w")
        link1.bind("<Button-1>", lambda e: webbrowser.open(DOWNLOAD_URL))

        icon_col = tk.Frame(header, bg=BG_COLOR)
        icon_col.pack(side="right", anchor="n")
        self._icon_img = None
        try:
            if ICON_PNG:
                self._icon_img = tk.PhotoImage(file=ICON_PNG)
                w = self._icon_img.width()
                if w > 110:
                    factor = max(1, round(w / 100))
                    self._icon_img = self._icon_img.subsample(factor, factor)
                tk.Label(icon_col, image=self._icon_img, bg=BG_COLOR).pack()
            else:
                raise FileNotFoundError
        except Exception:
            tk.Label(icon_col, text="[icon]", width=12, height=5, bg=BG_COLOR,
                     relief="groove").pack()
        cs = tk.Frame(icon_col, bg=BG_COLOR)
        cs.pack()
        tk.Label(cs, text="CS1", font=("Arial Black", 8, "bold"),
                 bg=BG_COLOR).pack(side="left")
        tk.Label(cs, text="CS2", font=("Arial Black", 8, "bold"),
                 bg=BG_COLOR).pack(side="left", padx=(10, 0))

        btns = tk.Frame(root, bg=BG_COLOR)
        btns.pack(fill="x", padx=16, pady=(8, 4))

        self.check_btn = tk.Button(btns, text="Check Path",
                                   command=self.on_check_path,
                                   bg=CHECKPATH_COLOR,
                                   activebackground=CHECKPATH_COLOR,
                                   font=("Segoe UI", 14, "bold"), height=1)
        self.check_btn.pack(fill="x", pady=(0, 6))

        self.solve_btn = tk.Button(btns, text="Solve", command=self.on_solve,
                                   bg=SOLVE_COLOR, activebackground=SOLVE_COLOR,
                                   font=("Segoe UI", 14, "bold"), height=1)
        self.solve_btn.pack(fill="x")

        self.log = scrolledtext.ScrolledText(root, height=6, font=("Consolas", 9),
                                             state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        self._log("Ready. Open your workbook in Excel and highlight the input range.")

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", str(msg) + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.root.update_idletasks()

    def on_solve(self):
        """Solve button: run the full Monte-Carlo, plot, and write results."""
        try:
            self._log("-" * 40)
            s = tol_stack_solve(StackRange(), log=self._log)
            if s is None:
                messagebox.showerror("TolStack", "INVALID INPUTS")
                return

            if s.Plot:
                plotting.plot_histogram(s.Error, s.mu, s.Nsig * s.sigma, s.Name)
                plotting.plot_coord2(COORD(), s.Tn_list, s.Name)
                plt.show(block=False)

            if s.Result is not None:
                from excel_io import write_results
                write_results(s.Result, s.uplusNsigma)
                self._log("Results written to Excel at "
                          f"row {s.Result[0]}, cols {s.Result[1] + 1}-{s.Result[1] + 6}.")

            self._log("mu+N*sigma = [" +
                      ", ".join(f"{v:.4e}" for v in s.uplusNsigma) + "]")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            traceback.print_exc()
            messagebox.showerror("TolStack", str(exc))

    def on_check_path(self):
        """Check Path button: plot the nominal coordinate path from Excel."""
        try:
            self._log("-" * 40)
            self._log("Checking path from active Excel selection...")
            s = fetchstack(StackRange())
            if s.R is None:
                messagebox.showerror("TolStack", "No R vectors found in selection.")
                return
            import numpy as np
            C = s.C if s.C is not None else np.zeros((1, 6))
            Cv = s.Cv if s.Cv is not None else np.zeros((1, 6))
            _, _, _, _, _, Tn_list, _ = solve_error_comp(
                s.R, np.zeros_like(np.atleast_2d(s.R)), C, Cv)
            plotting.plot_coord2(COORD(), Tn_list, s.Name or "Nominal Path")
            plt.show(block=False)
            self._log(f"Path plotted: {len(Tn_list)} coordinate frames.")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            traceback.print_exc()
            messagebox.showerror("TolStack", str(exc))


def main():
    root = tk.Tk()
    TolStackApp(root)
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main())
