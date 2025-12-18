# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File für Scrat-Backup
Erstellt ein Windows-Executable für die Backup-Anwendung
"""

import sys
from pathlib import Path

# Projekt-Pfade
project_root = Path.cwd()
src_path = project_root / "src"
assets_path = project_root / "assets"

# Icon-Pfad (nutze vorhandenes Icon)
icon_path = assets_path / "icons" / "scrat.ico"
if not icon_path.exists():
    icon_path = assets_path / "scrat_icon.ico"
if not icon_path.exists():
    icon_path = assets_path / "icons" / "scrat-256.png"
if not icon_path.exists():
    icon_path = None

# Hidden Imports für PySide6 und andere Module
hidden_imports = [
    # PySide6 Module
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',

    # Scrat-Backup Module
    'src.core.backup_engine',
    'src.core.restore_engine',
    'src.core.scanner',
    'src.core.compressor',
    'src.core.encryptor',
    'src.core.metadata_manager',
    'src.core.config_manager',
    'src.core.scheduler',
    'src.core.scheduler_worker',

    # Storage Backends
    'src.storage.usb_storage',
    'src.storage.sftp_storage',
    'src.storage.smb_storage',
    'src.storage.webdav_storage',
    'src.storage.rclone_storage',

    # GUI Module
    'src.gui.main_window',
    'src.gui.backup_tab',
    'src.gui.restore_tab',
    'src.gui.settings_tab',
    'src.gui.logs_tab',
    'src.gui.wizard',
    'src.gui.event_bus',
    'src.gui.system_tray',
    'src.gui.password_dialog',
    'src.gui.schedule_dialog',
    'src.gui.theme',

    # Utils
    'src.utils.validators',
    'src.utils.credential_manager',
    'src.utils.performance_logger',

    # Dependencies
    'py7zr',
    'cryptography',
    'paramiko',
    'webdavclient3',
    'smbprotocol',
    'keyring',
    'yaml',
    'dateutil',
    'sqlite3',
]

# Data Files (Assets, Config, etc.)
datas = []

# Assets-Ordner (Icons, etc.)
if assets_path.exists():
    datas.append((str(assets_path), 'assets'))

# Config-Vorlagen
config_path = project_root / "config"
if config_path.exists():
    datas.append((str(config_path), 'config'))

# Default Config
default_config = project_root / "default_config.json"
if default_config.exists():
    datas.append((str(default_config), '.'))

# Analysis
a = Analysis(
    ['src/main.py'],
    pathex=[str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'tkinter',
        '_tkinter',
    ],
    noarchive=False,
    optimize=0,
)

# PYZ (Python ZIP Archive)
pyz = PYZ(a.pure)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ScratBackup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Kein Console-Fenster (GUI-App)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path else None,
)

# COLLECT (sammelt alle Dateien für one-dir build)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ScratBackup',
)

# Optional: One-File Build (auskommentiert, da one-dir meist besser ist)
# exe = EXE(
#     pyz,
#     a.scripts,
#     a.binaries,
#     a.datas,
#     [],
#     name='ScratBackup',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     runtime_tmpdir=None,
#     console=False,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
#     icon=str(icon_path) if icon_path else None,
# )
