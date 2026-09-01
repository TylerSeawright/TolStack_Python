# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for TolStack (Python edition).
# Build with:  pyinstaller TolStack.spec
#
# Produces a single-file, windowed (no console) executable: dist/TolStack.exe

import os

block_cipher = None

# Bundle the icon assets. They may sit either next to this spec (if copied in)
# or one level up in the MATLAB folder; include whichever exist.
_candidates = [
    "TolStackIcon3.png",
    "TolStackIcon2.png",
    "TolStack.ico",
    os.path.join("..", "TolStackIcon3.png"),
    os.path.join("..", "TolStackIcon2.png"),
]
datas = [(p, ".") for p in _candidates if os.path.exists(p)]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["win32com", "win32com.client", "pythoncom", "pywintypes"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="TolStack",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # windowed app (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="TolStack.ico" if os.path.exists("TolStack.ico") else None,
)
