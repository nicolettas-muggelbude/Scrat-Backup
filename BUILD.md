# Build-Anleitung für Scrat-Backup

## Voraussetzungen

### System
- **Windows 10/11** oder **Ubuntu 22.04+** (je nach Zielplattform)
- **Python 3.12+**
- **Git**

### Python-Pakete

```bash
pip install -r requirements.txt
```

Wichtigste Build-Pakete:
- `pyinstaller>=6.0.0` – erstellt das Executable
- `PySide6>=6.6.0` – GUI-Framework

---

## Windows: Installer (.exe)

### Voraussetzungen (Windows)
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) installiert
- `iscc` im PATH (normalerweise `C:\Program Files (x86)\Inno Setup 6\`)

### Manuell bauen

```powershell
# 1. PyInstaller-Build
pyinstaller scrat_backup.spec --clean --noconfirm

# 2. Installer erstellen
iscc /DMyAppVersion=0.3.11 installer.iss

# Ergebnis: output\ScratBackup-v0.3.11-Setup.exe
```

### Installer-Details
- Installiert nach `%LocalAppData%\Scrat-Backup` (**kein Administratorrecht erforderlich**)
- Erstellt Startmenü-Einträge und optionalen Desktop-Shortcut
- Deinstallation über Windows Einstellungen

---

## Linux: AppImage

### Voraussetzungen (Linux)

```bash
# Ubuntu/Debian
sudo apt install python3-dev python3-venv libxcb-cursor0 libxcb-icccm4 \
                 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
                 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0

# appimagetool herunterladen
wget -O appimagetool "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
chmod +x appimagetool
```

### Manuell bauen

```bash
# 1. PyInstaller-Build
pyinstaller scrat_backup.spec --clean --noconfirm

# 2. AppDir-Struktur erstellen
mkdir -p AppDir/usr/bin
cp -r dist/ScratBackup/* AppDir/usr/bin/
# AppRun, .desktop und Icon hinzufügen (siehe CI-Workflow)

# 3. AppImage packen
./appimagetool AppDir ScratBackup-v0.3.11-x86_64.AppImage
```

Für Details zum AppDir-Layout siehe `.github/workflows/build-release.yml`.

---

## CI/CD: GitHub Actions

Builds werden automatisch ausgelöst wenn ein Tag mit `v*` gepusht wird:

```bash
git tag v0.3.11
git push origin v0.3.11
```

Der Workflow (`.github/workflows/build-release.yml`) baut:
- `build-windows` (windows-latest): PyInstaller → Inno Setup → `ScratBackup-vX.X.X-Setup.exe`
- `build-linux` (ubuntu-22.04): PyInstaller → appimagetool → `ScratBackup-vX.X.X-x86_64.AppImage`

Beide Artefakte werden automatisch als GitHub Release Assets hochgeladen.

---

## Build-Ausgabe (PyInstaller)

```
dist/
└── ScratBackup/
    ├── ScratBackup.exe      # Haupt-Executable
    ├── _internal/           # Python-Runtime & Dependencies
    └── assets/              # Icons etc.
```

Größe: ca. 130–180 MB (entpackt), ca. 60–80 MB (AppImage komprimiert)

---

## Versionsnummer angeben

Die Version wird an Inno Setup per Kommandozeile übergeben:

```powershell
iscc /DMyAppVersion=0.3.11 installer.iss
```

In der `installer.iss` ist definiert:
```
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
```

---

## Bekannte Probleme & Lösungen

### UPX deaktiviert
UPX-komprimierte Binaries lösen auf Windows Exploit Guard / DEP-Schutz aus
(`LoadLibrary: Unzulässiger Zugriff`). In `scrat_backup.spec` ist `upx=False` gesetzt –
**nicht ändern**.

### Import-Fehler beim Start
Fehlende Module zu `hiddenimports` in `scrat_backup.spec` hinzufügen:
```python
hiddenimports = [
    'dein_fehlendes_modul',
    # ...
]
```

### Templates werden nicht gefunden (AppImage)
AppImages laufen in einem read-only squashfs. Der `TemplateManager` nutzt
`sys._MEIPASS` für Bundle-Pfade – kein `mkdir` mehr im Bundle-Verzeichnis nötig.
Fallback: `~/.scrat-backup/templates/`

### Debug-Build (Console-Fenster anzeigen)
```python
# In scrat_backup.spec:
console=True  # statt console=False
```

### Long-Start (One-File-Build)
One-Directory-Build (Standard) bevorzugen. One-File entpackt beim Start alles
in ein Temp-Verzeichnis (langsam).

---

## Entwicklungsumgebung

```bash
git clone https://github.com/nicolettas-muggelbude/Scrat-Backup.git
cd Scrat-Backup
python3 -m venv venv
source venv/bin/activate     # Linux/macOS
# venv\Scripts\activate      # Windows
pip install -r requirements.txt
python3 src/main.py
```

---

*Erstellt mit [Claude Code](https://claude.com/claude-code)*
