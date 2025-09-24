# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for Image Tag Editor."""

import sys
from pathlib import Path
import os

block_cipher = None

# Get the project root directory
project_root = Path(os.getcwd())

a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / 'assets' / 'icon.ico'), '.'),
    ],
    hiddenimports=[
        'pandas',
        'numpy',
        'numpy.core',
        'numpy.core.multiarray',
        'numpy.core.umath',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'difflib',
        'webbrowser',
        'pathlib',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'PIL.ImageTk',
        'PIL._tkinter_finder',
    ],
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
    name='ImageTagEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'icon.ico'),  # Application icon
    version_file=None,
)
