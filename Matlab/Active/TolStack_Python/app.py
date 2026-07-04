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
        root.geometry("360x440")
        root.resizable(False, False)

        # Floating always-on-top panel (ACS-style), so it stays visible over
        # Excel while you work. Toggle with the "Pin on top" check box.
        self.pin_var = tk.BooleanVar(value=True)
        root.attributes("-topmost", True)
        try:
            root.lift()
        except Exception:
            pass

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

        self.export_btn = tk.Button(btns, text="Export Data", command=self.on_export,
                                    bg="#FFD966", activebackground="#FFD966",
                                    font=("Segoe UI", 12, "bold"), height=1)
        self.export_btn.pack(fill="x", pady=(6, 0))

        self.template_btn = tk.Button(btns, text="New Template", command=self.on_new_template,
                                      bg="#B4C7E7", activebackground="#B4C7E7",
                                      font=("Segoe UI", 12, "bold"), height=1)
        self.template_btn.pack(fill="x", pady=(6, 0))

        self.pin_chk = tk.Checkbutton(btns, text="Pin on top", variable=self.pin_var,
                                      command=self._toggle_pin, bg=BG_COLOR,
                                      activebackground=BG_COLOR, font=("Segoe UI", 9))
        self.pin_chk.pack(anchor="e", pady=(2, 0))

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
        """Solve: delegate to the shared headless backend (writes all outputs and
        embeds plots into the same sheet as the selection)."""
        self._run_backend("solve")

    def on_check_path(self):
        """Check Path: embed the nominal coordinate path plot into the sheet."""
        self._run_backend("checkpath")

    def on_new_template(self):
        """Insert a fresh TolStack template as a new tab in the active workbook."""
        try:
            import excel_io
            self._log("-" * 40)
            self._log("Adding a template tab to the active workbook...")
            name = excel_io.insert_template_tab()
            self._log(f"Template added as new tab '{name}'. Fill it in and click Solve.")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            traceback.print_exc()
            messagebox.showerror("TolStack", str(exc))

    def _toggle_pin(self):
        """Toggle the always-on-top (floating) behavior."""
        try:
            self.root.attributes("-topmost", bool(self.pin_var.get()))
        except Exception:
            pass

    def on_export(self):
        """Export the raw Monte-Carlo histogram samples to .csv or .xlsx."""
        try:
            from tkinter import filedialog
            import tolstack_cli
            from solver import run_solve
            self._log("-" * 40)
            self._log("Reading selection and running Monte-Carlo for export...")
            s, _sess = tolstack_cli._solve_live_stackrange()
            s = run_solve(s, log=self._log)
            if s is None:
                messagebox.showerror("TolStack", "INVALID INPUTS")
                return
            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV file", "*.csv"), ("Excel workbook", "*.xlsx")],
                initialfile=f"{s.Name or 'TolStack'}_histogram",
                title="Export histogram data")
            if not path:
                self._log("Export cancelled.")
                return
            tolstack_cli.export_histogram(s, path)
            self._log(f"Exported {s.N} samples ({len(s.Error)} rows) to {path}")
            messagebox.showinfo("TolStack", f"Exported {s.N} samples to:\n{path}")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            traceback.print_exc()
            messagebox.showerror("TolStack", str(exc))

    def _run_backend(self, mode):
        """Run tolstack_cli against the live Excel selection. This is the exact
        same code path the on-sheet Excel buttons use, so the mini-window and the
        in-Excel buttons behave identically."""
        try:
            self._log("-" * 40)
            self._log(f"Running '{mode}' on the active Excel selection...")
            import tolstack_cli
            rc = tolstack_cli.run_live(mode)
            if rc == 0:
                self._log("Done. Results and plots updated in Excel.")
            else:
                self._log("Finished with issues — see the pop-up message.")
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
# TolStack GUI: Check Path / Solve / Export Data buttons delegate to tolstack_cli.
