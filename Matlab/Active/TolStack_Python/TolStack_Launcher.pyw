"""TolStack_Launcher.pyw — one-click launcher for the TolStack app.

- On first run, checks for the required Python packages and pip-installs any
  that are missing (shows a small progress window; no console needed).
- Then opens the always-on-top TolStack window.

This is what the Excel add-in button (and the desktop shortcut) launches.
Uses only the standard library until the dependencies are present.
"""
import importlib.util
import os
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

# module name -> pip requirement
REQUIRED = {
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "openpyxl": "openpyxl",
    "win32com": "pywin32",   # Windows / live-Excel only
}


def _missing():
    miss = []
    for mod, pkg in REQUIRED.items():
        if mod == "win32com" and os.name != "nt":
            continue
        if importlib.util.find_spec(mod) is None:
            miss.append(pkg)
    return miss


def _pip_install(pkgs):
    """Install packages with the current interpreter's pip. Prefer
    requirements.txt if present so versions stay consistent."""
    req = os.path.join(HERE, "requirements.txt")
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
    if os.path.exists(req):
        cmd += ["-r", req]
    else:
        cmd += pkgs
    # Hide the console window on Windows.
    creationflags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
    return subprocess.run(cmd, capture_output=True, text=True,
                          creationflags=creationflags)


def _launch_app():
    import app  # imported only after deps are guaranteed present
    app.main()


def main():
    miss = _missing()
    if not miss:
        _launch_app()
        return

    # Show a tiny progress window while installing.
    import tkinter as tk
    from tkinter import messagebox
    win = tk.Tk()
    win.title("TolStack — first-time setup")
    win.geometry("360x120")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    tk.Label(win, text="Installing required packages:\n" + ", ".join(miss),
             font=("Segoe UI", 10), justify="left").pack(padx=16, pady=(16, 6), anchor="w")
    status = tk.Label(win, text="Please wait…", font=("Segoe UI", 9), fg="#555")
    status.pack(anchor="w", padx=16)
    result = {}

    def worker():
        result["proc"] = _pip_install(miss)

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    def poll():
        if t.is_alive():
            win.after(300, poll)
            return
        proc = result.get("proc")
        still = _missing()
        win.destroy()
        if still:
            out = (proc.stderr or proc.stdout or "") if proc else ""
            messagebox.showerror(
                "TolStack setup",
                "Could not install: " + ", ".join(still) +
                "\n\nTry running this once in a terminal:\n"
                f'"{sys.executable}" -m pip install ' + " ".join(still) +
                (("\n\n" + out[-600:]) if out else ""))
            return
        _launch_app()

    win.after(300, poll)
    win.mainloop()


if __name__ == "__main__":
    main()
