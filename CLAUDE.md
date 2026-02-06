# Scrat-Backup – CLAUDE.md

Verschlüsseltes, komprimiertes Backup-Tool mit Wizard-zentrierter Architektur und Template-System.

**Testanleitung:** `docs/TESTING.md`

---

## Architektur

```
Desktop-Starter (scrat-backup --wizard | --tray)
        ↓
SetupWizardV2  (src/gui/wizard_v2.py)
  StartPage → SourceSelectionPage → TemplateDestinationPage → SchedulePage → FinishPage
        ↓
System Tray  (Wizard öffnen | Backup starten | Hauptfenster)
```

**Normal-Modus:** Template-basierte, geführte Einrichtung → Tray startet.
**Experten-Modus:** MainWindow öffnet sich zusätzlich, volle Kontrolle.

---

## Projektstruktur (wichtige Dateien)

```
src/
├── gui/
│   ├── wizard_v2.py              # SetupWizardV2, Seiten-Routing, get_config()
│   ├── wizard_pages.py           # StartPage, SourceSelectionPage, FinishPage
│   ├── dynamic_template_form.py  # Dynamisches Formular aus Template-ui_fields
│   ├── theme_manager.py          # Dark/Light Mode, ACCENT_COLOR
│   ├── theme.py                  # get_color("primary") u.a. – zentrale Farbdefinition
│   ├── main_window.py            # MainWindow (Power-User)
│   └── run_wizard.py             # Wizard-Einstieg, QTranslator (deutsch)
├── core/
│   ├── template_manager.py       # Template laden, validieren, erstellen
│   ├── config_manager.py         # Konfigurationsverwaltung
│   ├── platform_scheduler.py     # Windows/Linux/macOS Scheduler (Factory)
│   └── autostart.py              # Autostart plattformunabhängig
├── templates/
│   ├── handlers/
│   │   ├── base.py               # TemplateHandler (ABC)
│   │   ├── usb_handler.py        # USB – Win/Linux/macOS Laufwerks-Erkennung
│   │   ├── onedrive_handler.py   # OneDrive – rclone + OAuth
│   │   ├── google_drive_handler.py
│   │   ├── dropbox_handler.py
│   │   ├── synology_handler.py   # SMB via net use / smbclient
│   │   ├── qnap_handler.py
│   │   └── nextcloud_handler.py  # WebDAV
│   └── (JSON-Definitionen werden vom TemplateManager geladen)
├── main.py                       # Einstiegspunkt, save_wizard_config(), start_backup_after_wizard()
└── templates/                    # *.json – usb, onedrive, synology, google_drive, dropbox, nextcloud, qnap
```

---

## Was ist fertig

- **Template-System:** TemplateManager, 7 Handler, 7 JSON-Definitionen
- **Wizard V3:** StartPage, SourceSelectionPage, TemplateDestinationPage, FinishPage – produktionsreif
- **DynamicTemplateForm:** Feldtypen text, password, combo, button, status, drive_selector, checkbox
- **Dark Mode:** ThemeManager mit Auto-Detection, Light/Dark Themes, ACCENT_COLOR globalisiert
- **Plattform-Abstraktionen:** PlatformScheduler (Win/Linux/macOS), AutostartManager
- **Barrierefreiheit:** Radio-Buttons, Tastatur-Navigation, Textfeld für Pfad-Eingabe, Schnellauswahl-Buttons
- **Lokalisierung:** QTranslator für deutsche Qt-Dialoge
- **USB-Template:** vollständig funktionsfähig inkl. drive_selector + Refresh
- **SchedulePage:** Zeitplan-Seite im Wizard – Auto-Checkbox, Frequenz (täglich/wöchentlich/monatlich/beim Start), Uhrzeit, Wochentage, Tag des Monats; dynamische Gruppen-Sichtbarkeit; gibt `schedule`-Config aus
- **Backup nach Wizard:** `start_backup_after_wizard()` in `main.py` – Fortschrittsanzeige (QProgressDialog ohne Abbrechen-Button), Thread-sichere Fortschritts-Updates, Multi-Threading aktiviert
- **App-Logo:** Eichel-Icon auf allen Fenstern (QApplication-Level `setWindowIcon` in `main.py` + `run_wizard.py`)
- **TemplateCard-Kacheln:** QFrame-basierte Kacheln mit 24px-Icons, Hover/Check-Styles, rahmenlos (ersetzt QPushButton)
- **USB-Erkennung Linux:** Robuste Username-Ermittlung (Fallbacks: $USER, getpass, pwd), `/media/USER/` ohne strenge removable-Prüfung (erkennt externe Festplatten)
- **MainWindow closeEvent:** Beendet Programm korrekt wenn kein Tray läuft, minimiert zu Tray nur wenn Tray sichtbar
- **SourceSelectionPage Edit-Modus:** Bei "Einstellungen ändern" werden vorhandene Quellen aus Config vorbefüllt (Standard-Bibliotheken + eigene Ordner)

---

## Aktuelle Fixes (2026-02-05/06)

### Windows
- ✅ **SchedulePage auf Windows sichtbar:** `nextId()` explizit gesetzt, `setFinalPage(True)` auf FinishPage
- ✅ **Nach Wizard kein MainWindow mehr:** Prüft jetzt `start_tray` Config – nur Tray oder MainWindow, nicht beides

### Linux/Ubuntu
- ✅ **Qt6 XCB-Dependencies:** libxcb-cursor0 + weitere XCB-Pakete in Docs (README.md, CLAUDE.md)
- ✅ **USB-Erkennung funktioniert:**
  - Username-Ermittlung mit Fallbacks (os.getlogin → $USER → getpass → pwd)
  - `/media/USER/*` ohne strenge removable-Prüfung (externe Festplatten haben removable=0)
  - Debug-Skript: `debug_usb.sh`
- ✅ **Wizard-Routing "edit":** Zeigt jetzt SourceSelectionPage mit vorbefüllten Quellen

### Performance
- ✅ **Multi-Threading Komprimierung:** py7zr nutzt jetzt `multithread=True` → alle CPU-Cores

### Bugfixes
- ✅ **MainWindow closeEvent:** Beendet sich korrekt ohne Tray (prüft `system_tray.is_visible()`)
- ✅ **QProgressDialog leerer Button:** `cancelButtonText=None` + `setCancelButton(None)`
- ✅ **isort & flake8 sauber:** Imports alphabetisch (Qt, QTime, Signal)

---

## Offene TODOs

### Wizard / GUI
- [x] **"Backup ändern" überspringt SourceSelectionPage** ✅ – "edit" routet jetzt über PAGE_SOURCE; SourceSelectionPage.initializePage() vorbefüllt aus Config
- [ ] Tray-Icon mit Theme-Toggle
- [ ] Restore-Flow (eigener Wizard)
- [x] Schedule-Page (Zeitplan im Wizard) ✅
- [ ] Encryption-Page (Verschlüsselung im Wizard)
- [ ] Template-Manager-Tab im MainWindow

### Templates & Handler
- [ ] Weitere Templates: iCloud, AWS S3, FTP, ownCloud, pCloud, **SFTP** (Community-Wunsch)
- [ ] Icons für Templates (aktuell: Emojis)
- [ ] Tests für alle Handler

### Linux / Packaging
- [ ] XDG User Directories Support (`xdg-user-dir`)
- [ ] Linux-Packaging: PyPI + .deb
- [ ] Desktop-Dateien (`scrat-backup.desktop`, `scrat-backup-tray.desktop`)
- [ ] GitHub Actions CI (Ubuntu / Windows / macOS Matrix)

### Zukunft
- [ ] Lokalisierung (DE/EN) – Strings externalisieren
- [ ] Multi-Destination: mehrere Backup-Ziele pro Durchlauf
- [ ] Template-Marketplace (Community-Templates aus URL importieren)
- [ ] Template-Wizard: eigene Templates aus bestehender Config erstellen
- [ ] Handler als Plugins (`~/.scrat-backup/plugins/`)
- [ ] Config-Migration: alte Destinations → Template-basiert

---

## Entscheidungen & Konventionen

| Thema | Entscheidung |
|-------|-------------|
| Template-Sichtbarkeit | **Permissiv:** Alle Templates anzeigen, Warnung bei fehlenden Requirements + Auto-Install |
| Cloud-Backends | Alle über **rclone** (OneDrive, Google Drive, Dropbox) |
| NAS-Backends | Alle über **SMB/smbclient** (Synology, QNAP) |
| Plattform-Strategie | EINE Code-Basis, plattformspezifische Handler-Zweige |
| Akzentfarbe | `ACCENT_COLOR = get_color("primary")` aus `theme.py` – niemals hard-coden |
| Benachrichtigungen | Qt-Tray-Messages als Fallback, plattformspezifisch als Option |
| Wizard nach Ersteinrichtung | StartPage zeigt Übersicht: Ändern / Ziel hinzufügen / Restore / Experten-Modus |
| Version im Wizard | Wird als Parameter von `run_wizard.py` übergeben, kein direkter Import |
| Credential-Speicher | `keyring` (Windows: DPAPI, Linux: SecretService/`secretstorage`) |
| USB-Destination-Typ | `destination["type"]` = template_id (`"usb"`), nicht `"local"` – Pfad aus `drive` + `path` zusammensetzen |
| Fortschritts-Dialog | QProgressDialog ohne Schließ-Button (`CustomizeWindowHint \| WindowTitleHint`), Fortschritt via shared dict zwischen Backup-Thread und Qt-Event-Loop |

### Wizard-Seitenfolge & Routing
- Page-IDs: `PAGE_START=0`, `PAGE_SOURCE=1`, `PAGE_MODE=2`, `PAGE_DESTINATION=3`, `PAGE_SCHEDULE=4`, `PAGE_FINISH=5`
- `nextId()` routet dynamisch basierend auf StartPage-Auswahl
- SchedulePage gibt `None` zurück wenn Auto-Zeitplan deaktiviert; sonst `{"enabled": True, "frequency", "time", "weekdays", "day_of_month"}`
- `sourcesChanged` Signal auf SourceSelectionPage aktiviert den Weiter-Button

### DynamicTemplateForm
- Formular wird aus `template.ui_fields` generiert
- Aktionen: `scan_shares()`, `test_connection()`, `oauth_login()`
- Validierung: required-Felder + Regex per Field-Definition

### Plattformspezifische Ausschlüsse (SourceSelectionPage)
- **Alle:** `*.tmp`, `*.cache`, `.git/`, `node_modules/`
- **Windows:** `Thumbs.db`, `desktop.ini`, `~$*`, `$RECYCLE.BIN/`
- **Linux:** `.Trash-*/`, `.thumbnails/`, `*.~lock.*`, `.directory`
- **macOS:** `.DS_Store`, `.AppleDouble/`, `.Spotlight-V100/`

---

## Linux-Dependencies

```bash
# Ubuntu/Debian
# Qt6 XCB-Abhängigkeiten (für GUI)
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
                 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0

# Scrat-spezifische System-Pakete
sudo apt install python3-keyring libsecret-1-0 smbclient cron

# Python (Linux-spezifisch)
pip install secretstorage python-notify2 pyxdg
```

---

## Session 2026-02-06: Performance & Edit-Modus Fixes

### Hauptprobleme gelöst:

#### 1. **OOM-Kills bei großen Dateien** ✅
- **Problem:** 6GB ISO-Datei verursachte "getötet" (Out of Memory)
- **Root Cause:** 
  - `encryptor.py:174` lädt gesamte Datei in RAM: `plaintext = f_in.read()`
  - Auch mit 128MB Split-Size: Eine große Datei = Ein großes Archiv
- **Lösung:**
  - **Chunked Encryption** implementiert (64MB Chunks)
  - Neues Format: `[SCRAT001][ChunkSize][Chunk1...][Chunk2...][End]`
  - Backward-kompatibel mit altem Format
  - RAM-Verbrauch: konstant ~64MB (statt 6GB+)

#### 2. **Extrem langsame Kompression** ✅
- **Problem:** KB pro 30 Sekunden (sollte MB/s sein)
- **Zwischenlösungen:**
  - Level 5 → Level 1 (5x schneller, aber immer noch langsam)
  - `multithread=True` hinzugefügt (Kompatibilitätsproblem mit alten py7zr)
- **Finale Lösung:**
  - **Kompression komplett deaktiviert** (FILTER_COPY)
  - Nur archivieren + verschlüsseln, keine Kompression
  - Datenrate: 128-200 MB/s ✅
  - Trade-off: Keine Platzeinsparung, aber funktionsfähig

#### 3. **Wizard-Architektur geändert** ✅
- **Vorher:** 
  - Erster Start → Wizard
  - Spätere Starts → MainWindow direkt
- **Jetzt:**
  - **IMMER** Wizard-Start
  - Im Wizard: Normal-Modus vs. Experten-Modus wählen
  - Nur bei Experten-Modus → MainWindow öffnet
- **Vorteil:** Settings-Änderungen sind immer zugänglich

#### 4. **Edit-Modus lädt keine Quellen** ✅
- **Probleme gefunden:**
  - `_prefilled` Flag verhinderte wiederholtes Laden
  - `wizard.field("start_action")` gab String `'None'` zurück statt `"edit"`
  - Checkboxen wurden nicht zurückgesetzt bei "backup"
  - Pfade matchten nicht (fehlende Normalisierung)
- **Lösungen:**
  - `_prefilled` Flag entfernt
  - Direkter Zugriff auf `wizard.start_page.selected_action`
  - IMMER Checkboxen zurücksetzen in `initializePage()`
  - `Path.resolve()` für beide Seiten des Vergleichs
  - Extensives Debug-Logging hinzugefügt

#### 5. **Config-Duplikate** ✅
- **Problem:** 7x Downloads, 7x USB-Laufwerk in Config
- **Root Cause:** Arrays wurden geleert aber nicht gespeichert
- **Lösung:** Explizites `save()` nach Löschen der Arrays

#### 6. **UI-Verbesserungen** ✅
- Schnellauswahl: Nur noch "Home" (Desktop/Dokumente waren Duplikate)

### Commits heute:
1. `cd61994` - fix: DEFAULT_SPLIT_SIZE auf 128MB reduziert (OOM-Fix)
2. `d0bca79` - feat: --wizard Parameter (später wieder entfernt)
3. `879bff0` - refactor: Wizard ist IMMER Einstiegspunkt
4. `a1bfabc` - fix: multithread-Parameter entfernt (Kompatibilität)
5. `2535381` - fix: Multi-Threading mit Fallback
6. `9f9e1a9` - perf: Kompression auf Level 1
7. `6208735` - perf: Kompression komplett deaktiviert (FILTER_COPY)
8. `7e1704a` - fix: Chunked Encryption (64MB)
9. `c81d71e` - fix: Quellen-Auswahl Pfad-Normalisierung
10. `f3ae50c` - fix: Config-Duplikate
11. `8b47df1` - fix: _prefilled Flag entfernt
12. `36487c9` - fix: Checkboxen IMMER zurücksetzen
13. `d990232` - debug: Massives Logging
14. `6e2e606` - fix: action direkt von StartPage
15. `5950051` - fix: Schnellauswahl vereinfacht

### Offene Punkte:
- [ ] Kompression wieder aktivieren (mit schnellerer Methode: zstd, gzip, oder System-7z)
- [ ] Tray-Start implementieren (aktuell TODO)
- [ ] Restore-Flow (eigener Wizard)


---

## Repository-Pfade

### Linux (Test-System):
```bash
/home/pcw-support/scrat
```

### Linux (Entwicklung):
```bash
/home/nicole/projekte/scrat-backup
```

### Windows:
```powershell
C:\Users\Nicole\projekte\scrat
```

**Synchronisation:** Via rsync über WSL `/mnt/c/`

## Updates zwischen Linux und Windows

**Von Linux → Windows kopieren:**
```bash
rsync -av --exclude 'venv/' --exclude '__pycache__/' --exclude '*.pyc' \
  /home/nicole/projekte/scrat-backup/ /mnt/c/Users/Nicole/projekte/scrat/
```

**Git Pull auf Windows:**
```powershell
cd C:\Users\Nicole\projekte\scrat
git pull
```

**Windows Virtual Environment neu erstellen:**
```powershell
cd C:\Users\Nicole\projekte\scrat
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .
```

