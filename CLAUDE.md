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
- **Wizard V3:** StartPage, SourceSelectionPage, TemplateDestinationPage, SchedulePage, EncryptionPage, RestoreWizardPage, FinishPage – produktionsreif
- **DynamicTemplateForm:** Feldtypen text, password, combo, button, status, drive_selector, checkbox
- **Dark Mode:** ThemeManager mit Auto-Detection, Light/Dark Themes, ACCENT_COLOR globalisiert
- **Plattform-Abstraktionen:** PlatformScheduler (Win/Linux/macOS), AutostartManager
- **Barrierefreiheit:** Radio-Buttons, Tastatur-Navigation, Textfeld für Pfad-Eingabe, Schnellauswahl-Buttons
- **Lokalisierung:** QTranslator für deutsche Qt-Dialoge
- **USB-Template:** vollständig funktionsfähig inkl. drive_selector + Refresh
- **SchedulePage:** Zeitplan-Seite im Wizard – Auto-Checkbox, Frequenz (täglich/wöchentlich/monatlich/beim Start), Uhrzeit, Wochentage, Tag des Monats; dynamische Gruppen-Sichtbarkeit; gibt `schedule`-Config aus
- **EncryptionPage:** Passwort + Bestätigung + Live-Validierung + Keyring-Speicherung; Passwort-Kette: wizard_config → keyring → Dialog
- **RestoreWizardPage:** DB-Modus (aus `~/.scrat-backup/metadata.db`) + Verzeichnis-Modus (manuell, sucht `metadata.db` im Backup-Ordner); Fortschrittsanzeige mit Phase, Dateinamen, Zähler
- **Backup nach Wizard:** `start_backup_after_wizard()` in `main.py` – Fortschrittsanzeige (QProgressDialog ohne Abbrechen-Button), Thread-sichere Fortschritts-Updates, Multi-Threading aktiviert
- **App-Logo:** Eichel-Icon auf allen Fenstern (QApplication-Level `setWindowIcon` in `main.py` + `run_wizard.py`)
- **TemplateCard-Kacheln:** QFrame-basierte Kacheln mit 24px-Icons, Hover/Check-Styles, rahmenlos; gesperrt wenn Backend nicht verfügbar (ForbiddenCursor)
- **USB-Erkennung Linux:** Robuste Username-Ermittlung (Fallbacks: $USER, getpass, pwd), `/media/USER/` ohne strenge removable-Prüfung (erkennt externe Festplatten)
- **MainWindow closeEvent:** Beendet Programm korrekt wenn kein Tray läuft, minimiert zu Tray nur wenn Tray sichtbar
- **SourceSelectionPage Edit-Modus:** Bei "Einstellungen ändern" werden vorhandene Quellen aus Config vorbefüllt (Standard-Bibliotheken + eigene Ordner)
- **System Tray vollständig verdrahtet:** `main.py` verbindet alle 5 Signals (start_backup, show_main_window, start_restore, show_settings, quit)
- **metadata.db auf Backup-Ziel:** Nach jedem Backup wird `metadata.db` automatisch auf das Zielmedium kopiert → Restore auf neuem System möglich
- **Rotation löscht Disk-Dateien:** `_rotate_old_backups()` entfernt `.enc`-Dateien via `shutil.rmtree()` (nicht nur DB-Einträge)
- **SFTP Host-Key-Sicherheit:** `RejectPolicy` + System-Known-Hosts; klare Fehlermeldung mit `ssh user@host` Anleitung bei unbekanntem Host
- **GitHub Actions CI:** `.github/workflows/build-release.yml` – baut Windows EXE + Linux AppImage automatisch bei `v*`-Tags
- **Release v0.3.0-beta:** Verfügbar auf GitHub mit Windows ZIP, Linux AppImage, Source ZIP
- **Log-Datei:** `_setup_logging()` in `main.py` schreibt immer in `%LocalAppData%\Scrat-Backup\scrat-backup.log` (Win) / `~/.scrat-backup/scrat-backup.log` (Linux)
- **Desktop-Benachrichtigungen:** `src/utils/notifications.py` – Linux: notify-send, Windows: PowerShell NotifyIcon, macOS: osascript; Tray-Backup nutzt `QSystemTrayIcon.showMessage`
- **Tray bleibt aktiv:** `setQuitOnLastWindowClosed(False)` – Wizard schließen beendet nicht die App
- **Wizard-Änderungen aus Tray gespeichert:** `_open_settings_wizard()` speichert Config + aktualisiert OS-Zeitplan
- **Restore-Seite scrollbar:** `QScrollArea` in `RestoreWizardPage` verhindert Quetschen beim Fortschrittsbalken
- **StartPage zeigt Version:** `version`-Parameter in `wizard_pages.py:StartPage.__init__`

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
- [x] **"Backup ändern" überspringt SourceSelectionPage** ✅
- [x] **Dark Mode: TemplateCard-Kacheln, Ordner-Liste, Ausschlüsse, Finish-Page** ✅
- [x] Tray vollständig verdrahtet ✅
- [x] Restore-Flow im Wizard (PAGE_RESTORE=6) ✅
- [x] Schedule-Page (Zeitplan im Wizard) ✅
- [x] Encryption-Page (Verschlüsselung im Wizard, PAGE_ENCRYPTION=7) ✅
- [ ] Tray-Icon mit Theme-Toggle
- [ ] Template-Manager-Tab im MainWindow
- [ ] WinRT AppId im Inno-Setup registrieren → „Scrat-Backup" statt „PowerShell" in Windows-Notifications

### Templates & Handler
- [ ] Weitere Templates: iCloud, AWS S3, FTP, ownCloud, pCloud, **SFTP** (Community-Wunsch)
- [ ] Icons für Templates (aktuell: Emojis)
- [ ] Tests für alle Handler

### Linux / Packaging
- [ ] XDG User Directories Support (`xdg-user-dir`)
- [ ] Linux-Packaging: PyPI + .deb
- [ ] Desktop-Dateien (`scrat-backup.desktop`, `scrat-backup-tray.desktop`)
- [x] GitHub Actions CI (Ubuntu + Windows) ✅
- [ ] macOS Build (GitHub Actions)

### Zukunft
- [ ] Lokalisierung (DE/EN) – Strings externalisieren
- [ ] Multi-Destination: mehrere Backup-Ziele pro Durchlauf
- [ ] Template-Marketplace (Community-Templates aus URL importieren)
- [ ] Template-Wizard: eigene Templates aus bestehender Config erstellen
- [ ] Handler als Plugins (`~/.scrat-backup/plugins/`)
- [ ] Config-Migration: alte Destinations → Template-basiert
- [ ] GitHub Actions auf Node.js 24 aktualisieren (Deadline Juni 2026; actions v5 abwarten)

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
- Page-IDs: `PAGE_START=0`, `PAGE_SOURCE=1`, `PAGE_MODE=2`, `PAGE_DESTINATION=3`, `PAGE_SCHEDULE=4`, `PAGE_FINISH=5`, `PAGE_RESTORE=6`, `PAGE_ENCRYPTION=7`
- `nextId()` routet dynamisch basierend auf StartPage-Auswahl
- Restore-Aktion: StartPage → PAGE_RESTORE (6) → fertig
- Normal/Experten-Modus: PAGE_SOURCE → PAGE_DESTINATION → PAGE_SCHEDULE → PAGE_ENCRYPTION → PAGE_FINISH
- SchedulePage gibt `None` zurück wenn Auto-Zeitplan deaktiviert; sonst `{"enabled": True, "frequency", "time", "weekdays", "day_of_month"}`
- EncryptionPage gibt Passwort in `get_config()["password"]` zurück; speichert optional im Keyring
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
  - **zstd-Kompression** (FILTER_ZSTD, Level 3) aktiviert (py7zr >= 0.20 / 1.0.0 ✅)
  - Fallback auf FILTER_COPY wenn FILTER_ZSTD nicht verfügbar
  - Datenrate: schnell (zstd ist ~5–10x schneller als LZMA) ✅
  - Split-Size: wieder auf 500MB zurückgesetzt

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
- [x] Kompression wieder aktivieren ✅ – zstd Level 3 via FILTER_ZSTD (py7zr 1.0.0)
- [ ] Tray-Start implementieren (aktuell TODO)
- [ ] Restore-Flow (eigener Wizard)

---

## Session 2026-03-24: Performance-Krise, Dark Mode Fixes

### Hauptprobleme gelöst:

#### 1. **9 Splits für 2GB, 14 Minuten → 2 Splits, 41 Sekunden** ✅
- **Root Cause:** `config.json` hatte denselben Quellpfad mehrfach – Ordner wurde ~10× gescannt und gepackt
- **Lösung:** Quellen in `main.py` werden vor dem Backup dedupliziert (`Path.resolve()`-Vergleich via `set`)

#### 2. **`compression_level=5` hardcoded in main.py** ✅
- `main.py` und `main_window.py` übergaben Level 5, ignorierten den Level-1-Default
- **Fix:** Überall `compression_level=1`; `BackupConfig`-Default ebenfalls auf 1 gesetzt

#### 3. **Temp-Speicher-Schätzung zu gering (1.9GB statt 2.9GB)** ✅
- Multiplikator 1.1× → 1.5× (zstd expandiert bereits komprimierte Dateien leicht)
- tmpfs `/tmp` auf Ubuntu mit 8GB RAM zu klein → Fallback-Kette: `/tmp` → `/var/tmp` → `~/.cache/scrat-backup/tmp`

#### 4. **Rotation löscht manuelle Backups** ✅
- **Anforderung:** Rotation nur bei automatisch ausgelösten (Scheduled) Backups, nie bei manuellen
- **Lösung:** `BackupConfig.auto_rotate: bool = False` – nur `main_window.py` (Schedule-Trigger) setzt `True`

#### 5. **Dark Mode: TemplateCard-Kacheln leuchtend weiß (Seite 3)** ✅
- `TemplateCard._update_style()` und `enterEvent` hatten hardcoded `white`/`#f5f5f5`
- **Fix:** `_is_dark_mode()` Hilfsfunktion (Palette-Check) in `wizard_v2.py`; alle Zustände theme-aware

#### 6. **Dark Mode: Eigene-Ordner-Liste leuchtend weiß (Seite 2)** ✅
- `custom_list` hatte `background-color: white`
- **Fix:** `_update_custom_list_style()` + ClickableFrame-Hover nutzen `_is_dark_mode()`

#### 7. **Dark Mode: Ausschlüsse-Label** ✅
- `excludes_label`: `#f5f5f5` → `#252525` im Dark Mode

#### 8. **Passwort-Dialog zeigt Windows-Text auf Linux** ✅
- Checkbox/Info-Text zeigte immer "Windows Credential Manager"
- **Fix:** `platform.system()` → Windows / macOS / Linux-spezifischer Text

#### 9. **Dark Mode: Letzte Wizard-Seite (leuchtende Rahmen)** ✅
- `backup_group` / `tray_group`: fixer Rahmen `#e0e0e0` → `#3f3f3f` im Dark Mode
- `success_label`: Hellgrün → dunkles Grün im Dark Mode
- Styles werden in `initializePage()` gesetzt (Theme zum Anzeige-Zeitpunkt)

### Commits dieser Session:
1. `e417d4a` - fix: Quell-Duplikate entfernen und Kompression auf Level 1 setzen
2. `4feaa2c` - feat: Rotation nur bei automatischen Backups, nie bei manuellen
3. `4281e3a` - fix: Dark Mode TemplateCard-Kacheln + Eigene-Ordner-Liste
4. `cb153a4` - fix: Dark Mode Ausschlüsse-Label + Passwort-Dialog plattformspezifisch
5. `59a5d85` - fix: Dark Mode letzte Wizard-Seite

### Offene Punkte nach dieser Session:
- [x] Tray-Start implementieren ✅ (Session 2026-04-08)
- [x] Restore-Flow ✅ (Session 2026-04-08)
- [x] `_rotate_old_backups()`: löscht jetzt Disk-Dateien ✅ (Session 2026-04-08)
- [ ] Dark Mode: weitere hardcodierte Farben in anderen Tabs/Dialogen prüfen

---

## Session 2026-04-08: Beta-Release v0.3.0-beta

### Hauptprobleme gelöst:

#### 1. **Restore-Flow im Wizard** ✅
- **PAGE_RESTORE (6):** Neue Wizard-Seite mit 2 Modi
  - **DB-Modus:** lädt automatisch aus `~/.scrat-backup/metadata.db` (vorhandene Konfiguration)
  - **Verzeichnis-Modus:** Backup-Ordner manuell wählen, `metadata.db` wird automatisch gesucht (neues System)
  - Vollständige Fortschrittsanzeige (Phase, Dateizähler, aktuellem Dateinamen)
- Routing: `StartPage.nextId()` → PAGE_RESTORE bei action="restore"

#### 2. **Encryption-Page im Wizard** ✅
- **PAGE_ENCRYPTION (7):** Passwort + Bestätigung, Live-Validierung, optionale Keyring-Speicherung
- Routing: SchedulePage.nextId() → PAGE_ENCRYPTION → PAGE_FINISH
- Passwort-Kette in `start_backup_after_wizard()`: wizard_config → keyring → Dialog

#### 3. **System Tray vollständig verdrahtet** ✅
- `main.py run_gui()`: alle 5 Signals verbunden (war zuvor auskommentiertes TODO)
- `start_restore` öffnet Wizard direkt auf PAGE_RESTORE

#### 4. **metadata.db auf Backup-Ziel kopieren** ✅
- `backup_engine._copy_db_to_destination()`: nach jedem Backup (full/incremental/keine Änderungen)
- Fehler nicht-fatal (Backup trotzdem erfolgreich)
- Ermöglicht Restore auf neuem System ohne Originalrechner

#### 5. **Rotation löscht Disk-Dateien** ✅
- `_rotate_old_backups()`: `shutil.rmtree(backup_dir)` für physisches Löschen
- Vorher: nur DB-Einträge gelöscht, `.enc`-Dateien blieben auf Disk

#### 6. **SFTP Host-Key-Sicherheit** ✅
- `AutoAddPolicy` → `RejectPolicy` + `load_system_host_keys()`
- Zusätzlich: `~/.scrat-backup/known_hosts` als projektspezifische Known-Hosts
- Klare Fehlermeldung: `ssh username@host` ausführen, dann retry

#### 7. **TemplateCard sperrt nicht verfügbare Backends** ✅
- `mousePressEvent`: blockiert Klick wenn `not self._is_available`
- Cursor wechselt zu `Qt.CursorShape.ForbiddenCursor` bei nicht-installierten Backends (rclone, smbclient)

#### 8. **PyInstaller-Optimierung (87MB → ~70MB AppImage)** ✅
- `scrat_backup.spec` vollständig überarbeitet:
  - Explizite `hidden_imports` (nur gebrauchte Module)
  - `hooksconfig` für PySide6 QML-Plugin-Ausschluss
  - Große `excludes`-Liste (Qt6Quick, Qml, Pdf, Multimedia, Bluetooth, WebEngine, 3D)
  - `remove_qt_libs()`: filtert Qt-`.so`-Dateien post-Analyse
  - `strip=True` in EXE + COLLECT, `optimize=1` in PYZ
  - `glob.glob()` Loop statt Glob-Pattern in datas (verhindert FileNotFoundError)

#### 9. **GitHub Actions CI** ✅
- `.github/workflows/build-release.yml`: ausgelöst bei `v*`-Tags
- `build-windows` (windows-latest): EXE → ZIP → Release-Upload
- `build-linux` (ubuntu-22.04): apt-deps → appimagetool → AppImage → Release-Upload
- `softprops/action-gh-release@v2` mit `permissions: contents: write`

### Commits dieser Session:
1. `41c2b57` - fix: venv-Aktivierung in Linux/macOS Installations-Anleitungen
2. `1b624fc` - docs: Session 2026-03-24 dokumentiert, README + CONTRIBUTING aktualisiert
3. *(Viele Commits für Beta-Features, Encryption-Page, Restore-Flow, Tray, CI)*

### Release v0.3.0-beta Assets (GitHub):
- `ScratBackup-v0.3.0-beta-windows.zip` (CI: Windows EXE)
- `ScratBackup-v0.3.0-beta-x86_64.AppImage` (CI: Linux AppImage)
- `scrat-backup-v0.3.0-beta-source.zip` (manuell)

### Offene Punkte nach dieser Session:
- [ ] Node.js 20 Deprecation in GitHub Actions (Deadline Juni 2026; auf v5 Actions warten)
- [ ] macOS-Build (kein macOS-Runner aktuell konfiguriert)
- [ ] Dark Mode: weitere hardcodierte Farben in anderen Tabs/Dialogen

---

## Session 2026-04-09: Packaging-Fixes, Auto-Updater, Template-JSONs

### Hauptprobleme gelöst:

#### 1. **Windows: python312.dll LoadLibrary-Fehler** ✅
- Installer installierte nach `C:\Program Files\` → DEP/CFG blockierte DLL
- Fix: `{autopf}` → `{localappdata}`, `PrivilegesRequired=lowest`
- UPX-Komprimierung war zweite Ursache → `upx=False` in EXE + COLLECT

#### 2. **Linux/Windows: App startet nicht (NameError)** ✅
- `QPushButton`, `QTableWidget`, `QProgressBar`, `QFileDialog` fehlten in `wizard_v2.py`
- `from src import __version__` schlug im PyInstaller-Bundle fehl → Fallback eingebaut

#### 3. **Linux: TemplateManager read-only Fehler** ✅
- `_get_system_templates_dir()` versuchte `mkdir` im AppImage (squashfs, read-only)
- Fix: `sys._MEIPASS` für Bundle-Pfad, schreibbarer Fallback `~/.scrat-backup/templates/`

#### 4. **Template-JSONs fehlten komplett** ✅
- 7 JSON-Definitionen waren nie im Repo vorhanden
- Erstellt: `usb.json`, `nextcloud.json`, `onedrive.json`, `google_drive.json`,
  `dropbox.json`, `synology.json`, `qnap.json`

#### 5. **Windows Installer → Inno Setup statt ZIP** ✅
- `installer.iss`: Version per `/DMyAppVersion=` aus CI übergeben
- CI baut `ScratBackup-vX.X.X-Setup.exe` statt ZIP

#### 6. **Auto-Updater implementiert** ✅
- `src/core/update_checker.py`: QThread, GitHub Releases API, einmal täglich
- `src/gui/update_dialog.py`: Dialog mit Release Notes + Download-Button
- Plattformspezifischer Download-Link (Setup.exe / AppImage)

#### 7. **pip install -r requirements.txt im CI** ✅
- `pyproject.toml` hat keine `dependencies`-Sektion
- `pip install -e ".[dev]"` installierte nichts → PySide6 fehlte im Bundle

### Release v0.3.11-beta:
- Windows + Linux starten ✅
- 7 Templates geladen ✅
- Inno Setup Installer (kein Admin nötig) ✅
- Auto-Updater aktiv ✅

---

## Session 2026-04-09: Bugfixes, Desktop-Notifications, Tray-Verbesserungen (v0.3.16–v0.3.24)

### Hauptprobleme gelöst:

#### 1. **App startet nicht (TypeError beim Start)** ✅
- **Root Cause:** `wizard_v2.py` übergibt `version=version` an `StartPage`, aber `StartPage.__init__` in `wizard_pages.py` akzeptierte keinen `version`-Parameter
- **Fix:** `StartPage.__init__(self, parent=None, version: str = "")` in `wizard_pages.py`; Version erscheint jetzt im Untertitel der ersten Wizard-Seite

#### 2. **Log-Datei für Fehlerdiagnose** ✅
- `console=False` in PyInstaller schluckt alle Exceptions lautlos
- **Fix:** `_setup_logging()` in `main.py` schreibt immer in Datei:
  - Windows: `%LocalAppData%\Scrat-Backup\scrat-backup.log`
  - Linux: `~/.scrat-backup/scrat-backup.log`

#### 3. **Desktop-Benachrichtigungen für automatische Backups** ✅
- Neu: `src/utils/notifications.py` – plattformübergreifend
  - **Linux:** `notify-send`
  - **Windows (Headless):** PowerShell `NotifyIcon` (zeigt „PowerShell" im Header – WinRT-Ansatz nicht zuverlässig, zurückgestellt)
  - **macOS:** `osascript`
- Tray-Backup: `tray.show_backup_started()` / `show_backup_completed()` / `show_backup_failed()` via `QSystemTrayIcon.showMessage`
- `start_backup_after_wizard()` gibt jetzt `bool` zurück (True=Erfolg)

#### 4. **Tray beendet sich beim Schließen von Wizard-Fenstern** ✅
- **Root Cause:** Qt beendet App wenn letztes Fenster geschlossen wird
- **Fix:** `app.setQuitOnLastWindowClosed(False)` in `run_gui()`

#### 5. **Wizard-Änderungen aus Tray werden nicht gespeichert** ✅
- **Root Cause:** `_open_settings_wizard()` öffnete Wizard, wertete Ergebnis nie aus
- **Fix:** `if w.exec(): save_wizard_config(new_config); _activate_os_schedule(...)` in `_open_settings_wizard()`

#### 6. **Restore-Seite: Einstellungen werden gequetscht** ✅
- **Root Cause:** `QVBoxLayout` presst alle Widgets in die feste Wizard-Höhe wenn Fortschrittsbereich eingeblendet wird
- **Fix:** `QScrollArea` als äußerer Container in `RestoreWizardPage._setup_ui()`

#### 7. **„Vorhandene Dateien überschreiben" nur bei Original-Ordner wählbar** ✅
- **Root Cause:** Checkbox war per `stateChanged` an „In Original-Verzeichnisse"-Checkbox gekoppelt
- **Fix:** Kopplung entfernt – Option ist immer frei wählbar

#### 8. **WinRT Toast-Notifications (nicht umgesetzt)** ⚠️
- Versuch: `ToastNotificationManager::CreateToastNotifier('Scrat-Backup')` – hätte „Scrat-Backup" statt „PowerShell" im Header gezeigt
- Problem: Benachrichtigungen blieben komplett aus (AppId nicht in Windows-Registry registriert)
- **Zurückgestellt** – Lösung wäre AppId-Registrierung im Inno-Setup-Installer

### Neue Dateien:
- `src/utils/notifications.py` – plattformübergreifende Desktop-Notifications (Headless-Modus)

### Geänderte Dateien:
- `src/main.py` – `_setup_logging()`, `setQuitOnLastWindowClosed(False)`, `_open_settings_wizard()` speichert, `start_backup_after_wizard()` returns bool
- `src/gui/wizard_pages.py` – `StartPage.__init__` akzeptiert `version`-Parameter
- `src/gui/wizard_v2.py` – `RestoreWizardPage`: QScrollArea, `_overwrite_checkbox` entkoppelt

### Releases dieser Session:
- v0.3.16 – Desktop-Notifications
- v0.3.17 – Log-Datei (Hotfix für Debugging)
- v0.3.18 – StartPage TypeError Fix (App startet wieder)
- v0.3.19 – WinRT Toast (zurückgezogen)
- v0.3.20 – `setQuitOnLastWindowClosed(False)` + Popup-Fallback
- v0.3.21 – Wizard-Änderungen aus Tray werden gespeichert
- v0.3.22 – Revert auf PowerShell NotifyIcon
- v0.3.23 – Restore-Seite scrollbar
- v0.3.24 – „Überschreiben" unabhängig wählbar

### Offene Punkte nach dieser Session:
- [ ] Linux-Test: AppImage, Tray, notify-send, crontab (geplant 2026-04-10)
- [ ] WinRT AppId im Inno-Setup registrieren → saubere Toast-Notifications
- [ ] Dark Mode: weitere hardcodierte Farben in anderen Tabs/Dialogen prüfen

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

