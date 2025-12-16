# 🔨 Build-Anleitung für Scrat-Backup

Diese Anleitung beschreibt, wie du Scrat-Backup als eigenständiges Windows-Executable bauen kannst.

## 📋 Voraussetzungen

### System
- **Windows 10/11** (empfohlen für Windows-Build)
- **Python 3.11+** installiert
- **Git** für Repository-Cloning

### Python-Pakete
Alle benötigten Pakete sind in `requirements.txt` aufgelistet:

```bash
pip install -r requirements.txt
```

Wichtigste Pakete für den Build:
- `pyinstaller>=6.0.0` - Erstellt das Executable
- `PyQt6>=6.6.0` - GUI-Framework
- Alle weiteren Runtime-Dependencies

## 🚀 Build-Prozess

### Methode 1: Automatisches Build-Script (Empfohlen)

Das Projekt enthält ein automatisches Build-Script:

```bash
python build_exe.py
```

**Optionen:**
```bash
# Ohne Bereinigung alter Builds
python build_exe.py --skip-clean

# Ohne ZIP-Archiv-Erstellung
python build_exe.py --no-zip

# Hilfe anzeigen
python build_exe.py --help
```

Das Script führt automatisch aus:
1. ✓ Bereinigung alter Build-Verzeichnisse
2. ✓ Prüfung aller Dependencies
3. ✓ Icon-Validierung
4. ✓ PyInstaller-Build
5. ✓ ZIP-Archiv-Erstellung für Distribution

### Methode 2: Manuell mit PyInstaller

Für erweiterte Kontrolle kannst du PyInstaller direkt verwenden:

```bash
# One-Directory Build (empfohlen)
pyinstaller scrat-backup.spec --clean --noconfirm

# One-File Build (langsamer Start, aber eine Datei)
# Bearbeite scrat-backup.spec und kommentiere One-File-Abschnitt ein
pyinstaller scrat-backup.spec --clean --noconfirm --onefile
```

## 📂 Build-Ausgabe

Nach erfolgreichem Build findest du:

```
dist/
└── ScratBackup/
    ├── ScratBackup.exe          # Haupt-Executable
    ├── _internal/                # Python-Runtime & Dependencies
    ├── assets/                   # Icons, Themes, etc.
    └── config/                   # Konfigurations-Vorlagen
```

**Größe:** Ca. 150-200 MB (entpackt)

## 🧪 Build testen

1. Navigiere zum Build-Verzeichnis:
   ```bash
   cd dist/ScratBackup
   ```

2. Starte das Executable:
   ```bash
   ScratBackup.exe
   ```

3. Teste Kernfunktionen:
   - ✓ GUI startet ohne Fehler
   - ✓ Wizard wird beim ersten Start angezeigt
   - ✓ Quellen/Ziele können hinzugefügt werden
   - ✓ Backup-Engine funktioniert
   - ✓ Restore-Engine funktioniert
   - ✓ Einstellungen können gespeichert werden

## 📦 Distribution

### ZIP-Archiv

Das Build-Script erstellt automatisch ein ZIP-Archiv:

```
dist/ScratBackup-v0.2.0-beta-windows.zip
```

Dieses kann direkt an Benutzer verteilt werden. Sie müssen nur:
1. ZIP entpacken
2. `ScratBackup.exe` starten
3. Setup-Wizard durchlaufen

### Windows Installer (Optional)

Für professionellere Distribution kannst du einen Installer mit **Inno Setup** erstellen:

1. Installiere [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Verwende das bereitgestellte Script: `installer.iss`
3. Compile mit Inno Setup Compiler

Der Installer:
- Erstellt Startmenü-Einträge
- Fügt Deinstallations-Option hinzu
- Kann Desktop-Shortcut erstellen
- Registriert die Anwendung in Windows

## 🐛 Häufige Probleme

### Import-Fehler beim Start

**Problem:** `ModuleNotFoundError` oder `ImportError` beim Start des EXE

**Lösung:** Füge fehlende Module zu `hiddenimports` in `scrat-backup.spec` hinzu:

```python
hiddenimports = [
    'dein_fehlendes_modul',
    # ...
]
```

### Icon wird nicht angezeigt

**Problem:** Executable hat kein Icon oder Standard-Python-Icon

**Lösung:**
- Stelle sicher dass `assets/icons/scrat.ico` existiert
- Format muss .ICO sein (nicht PNG oder SVG)
- Rebuild mit: `python build_exe.py`

### Lange Startzeit

**Problem:** One-File Build startet langsam (10-30 Sekunden)

**Lösung:**
- Verwende **One-Directory Build** (Standard in `scrat-backup.spec`)
- One-File entpackt beim Start alles in Temp-Ordner

### UPX-Komprimierungs-Fehler

**Problem:** Build schlägt fehl mit UPX-Fehler

**Lösung:**
```python
# In scrat-backup.spec:
upx=False  # statt upx=True
```

### Antivirus False Positive

**Problem:** Antivirus markiert EXE als verdächtig

**Lösung:**
- PyInstaller-EXEs werden manchmal fälschlich erkannt
- Code-Signing-Zertifikat besorgen (für echte Releases)
- Bei VirusTotal hochladen für Reputation
- Whitelist-Exception in Antivirus erstellen

## 🔧 Build-Konfiguration anpassen

### Eigenes Icon verwenden

Ersetze `assets/icons/scrat.ico` mit deinem Icon oder ändere in `scrat-backup.spec`:

```python
icon_path = Path("dein/pfad/zum/icon.ico")
```

### Versionsnummer ändern

Aktualisiere in mehreren Dateien:
1. `src/gui/main_window.py` → Version-Label im Info-Tab
2. `build_exe.py` → Header-Version
3. `setup.py` (falls vorhanden)

### One-File Build aktivieren

In `scrat-backup.spec` am Ende:
1. Kommentiere `COLLECT(...)` aus
2. Aktiviere den One-File `EXE(...)` Abschnitt

### Konsolen-Fenster anzeigen (Debug)

Für Debugging kann Console-Fenster hilfreich sein:

```python
# In scrat-backup.spec:
console=True  # statt console=False
```

## 📊 Build-Optimierung

### Reduziere Größe

1. **Exclude unnötige Module:**
   ```python
   excludes=['matplotlib', 'numpy', 'scipy', 'pandas', 'PIL', 'tkinter']
   ```

2. **UPX-Komprimierung aktivieren:**
   ```python
   upx=True
   upx_exclude=[]
   ```

3. **Strip Debug-Symbols:**
   ```python
   strip=True  # Nur auf Linux/Mac
   ```

### Schnellere Builds

1. Verwende `--skip-clean` wenn du mehrfach buildest:
   ```bash
   python build_exe.py --skip-clean
   ```

2. PyInstaller-Cache nutzen (Standard aktiv)

## 🌐 Cross-Platform Builds

### Windows-Build von Linux/Mac

**Nicht empfohlen!** PyInstaller erstellt plattformspezifische Builds.

**Alternativen:**
- Virtual Machine mit Windows
- GitHub Actions CI/CD (siehe `.github/workflows/build.yml`)
- Docker mit Wine (komplex, nicht empfohlen)

### Empfehlung

Baue immer auf der Ziel-Plattform:
- Windows EXE → Build auf Windows
- macOS App → Build auf macOS
- Linux Binary → Build auf Linux

## 📝 CI/CD mit GitHub Actions

Für automatische Builds bei jedem Release kannst du GitHub Actions verwenden.

Beispiel-Workflow: `.github/workflows/build.yml`

```yaml
name: Build Windows EXE

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Build with PyInstaller
      run: python build_exe.py

    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: ScratBackup-Windows
        path: dist/ScratBackup-*.zip
```

## 💡 Best Practices

1. **Teste gründlich** nach jedem Build
2. **Version-Tags** verwenden für Releases (`v0.2.0-beta`)
3. **Clean Builds** vor Releases
4. **Multiple PCs** testen wenn möglich
5. **Antivirus-Scan** vor Distribution
6. **Changelog** pflegen
7. **Backup** der Build-Konfiguration in Git

## 🆘 Support

Bei Problemen:
1. Prüfe [PyInstaller Dokumentation](https://pyinstaller.org/en/stable/)
2. Suche in [PyInstaller Issues](https://github.com/pyinstaller/pyinstaller/issues)
3. Erstelle Issue in diesem Repository
4. Debug-Build mit `console=True` erstellen

---

**Happy Building! 🎉**

*Erstellt mit [Claude Code](https://claude.com/claude-code)*
