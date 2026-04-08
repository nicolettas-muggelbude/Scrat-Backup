# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File für Scrat-Backup
"""

import sys
from pathlib import Path

project_root = Path.cwd()
src_path = project_root / "src"
assets_path = project_root / "assets"

icon_path = assets_path / "icons" / "scrat.ico"
if not icon_path.exists():
    icon_path = assets_path / "icons" / "scrat-256.png"
if not icon_path.exists():
    icon_path = None

# Nur die Module die wir wirklich brauchen
hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',

    'src.core.backup_engine',
    'src.core.restore_engine',
    'src.core.scanner',
    'src.core.compressor',
    'src.core.encryptor',
    'src.core.metadata_manager',
    'src.core.config_manager',
    'src.core.scheduler',
    'src.core.scheduler_worker',
    'src.core.autostart',
    'src.core.platform_scheduler',
    'src.core.template_manager',

    'src.storage.usb_storage',
    'src.storage.sftp_storage',
    'src.storage.smb_storage',
    'src.storage.webdav_storage',
    'src.storage.rclone_storage',

    'src.gui.main_window',
    'src.gui.backup_tab',
    'src.gui.restore_tab',
    'src.gui.settings_tab',
    'src.gui.logs_tab',
    'src.gui.wizard_v2',
    'src.gui.wizard_pages',
    'src.gui.dynamic_template_form',
    'src.gui.event_bus',
    'src.gui.system_tray',
    'src.gui.password_dialog',
    'src.gui.schedule_dialog',
    'src.gui.theme',
    'src.gui.theme_manager',
    'src.gui.run_wizard',
    'src.gui.update_dialog',
    'src.core.update_checker',

    'src.templates.handlers.usb_handler',
    'src.templates.handlers.onedrive_handler',
    'src.templates.handlers.google_drive_handler',
    'src.templates.handlers.dropbox_handler',
    'src.templates.handlers.nextcloud_handler',
    'src.templates.handlers.synology_handler',
    'src.templates.handlers.qnap_handler',

    'src.utils.validators',
    'src.utils.credential_manager',
    'src.utils.performance_logger',

    'py7zr',
    'cryptography',
    'paramiko',
    'keyring',
    'yaml',
    'dateutil',
    'sqlite3',
    'webdavclient3',
]

datas = []
if assets_path.exists():
    datas.append((str(assets_path), 'assets'))

# Templates-JSON einbinden (nur wenn vorhanden)
templates_path = project_root / "src" / "templates"
import glob as _glob
for _jf in _glob.glob(str(templates_path / "*.json")):
    datas.append((_jf, 'src/templates'))

a = Analysis(
    ['src/main.py'],
    pathex=[str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={
        # Nur benötigte Qt-Module einbinden
        "pyside6": {
            "excluded_qml_plugins": [
                "QtQuick", "QtQuick3D", "QtCharts", "QtDataVisualization",
                "QtMultimedia", "QtBluetooth", "QtLocation", "QtNfc",
                "QtSensors", "QtWebSockets",
            ],
        },
    },
    runtime_hooks=[],
    excludes=[
        # Schwergewichtige Qt-Module die wir nicht nutzen
        'PySide6.QtQuick',
        'PySide6.QtQuick3D',
        'PySide6.QtQml',
        'PySide6.QtQmlModels',
        'PySide6.QtQmlCore',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtBluetooth',
        'PySide6.QtLocation',
        'PySide6.QtPositioning',
        'PySide6.QtNfc',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtWebSockets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DExtras',
        'PySide6.QtTextToSpeech',
        'PySide6.QtRemoteObjects',
        'PySide6.QtStateMachine',
        'PySide6.QtDesigner',
        'PySide6.QtHelp',
        'PySide6.QtUiTools',
        'PySide6.QtAxContainer',

        # Ungenutzte Python-Pakete
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'tkinter',
        '_tkinter',
        'lxml',
        'wx',
        'gi',
        'gtk',
        'test',
        'unittest',
        'doctest',
        'pdb',
        'profile',
        'pstats',
        'cProfile',
        'difflib',
    ],
    noarchive=False,
    optimize=1,  # Entfernt Docstrings → kleinere .pyc
)

# Unnötige Qt-Libs nach der Analyse manuell herausfiltern
def remove_qt_libs(binaries, patterns):
    """Entfernt Qt-Bibliotheken die wir nicht brauchen."""
    import re
    filtered = []
    for (dest, source, kind) in binaries:
        skip = any(re.search(p, dest, re.IGNORECASE) for p in patterns)
        if not skip:
            filtered.append((dest, source, kind))
    return filtered

unused_qt_libs = [
    r'Qt6Quick',
    r'Qt6Qml',
    r'Qt6QmlMeta',
    r'Qt6QmlModels',
    r'Qt6QmlWorkerScript',
    r'Qt6Pdf',
    r'Qt6Multimedia',
    r'Qt6Bluetooth',
    r'Qt6Location',
    r'Qt6Positioning',
    r'Qt6VirtualKeyboard',
    r'Qt6Charts',
    r'Qt63D',
    r'Qt6TextToSpeech',
    r'Qt6WebEngine',
    r'Qt6RemoteObjects',
    r'Qt6StateMachine',
    r'Qt6Designer',
]

a.binaries = remove_qt_libs(a.binaries, unused_qt_libs)

pyz = PYZ(a.pure, optimize=1)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ScratBackup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,   # UPX deaktiviert – verursacht LoadLibrary-Fehler auf Windows
    console=False,
    icon=str(icon_path) if icon_path else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,   # UPX deaktiviert – verursacht LoadLibrary-Fehler auf Windows
    name='ScratBackup',
)
