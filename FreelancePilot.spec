# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for FreelancePilot.
Builds a production Windows standalone executable bundle.
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all qtawesome fonts and icons
qtawesome_datas = collect_data_files('qtawesome')

datas = [
    ('assets', 'assets'),
] + qtawesome_datas

hiddenimports = [
    'qtawesome',
    'sqlalchemy.dialects.sqlite',
    'reportlab',
    'reportlab.platypus',
    'reportlab.lib.colors',
    'keyring.backends.Windows',
    'pydantic',
    'google.genai',
    'groq',
] + collect_submodules('qtawesome')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FreelancePilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Windowed desktop application (no cmd prompt)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='FreelancePilot',
)
