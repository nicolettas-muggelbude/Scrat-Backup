# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [0.3.12-beta] - 2026-04-09

### Fixed
- **USB-Backup: Formular komplett leer** – `DynamicTemplateForm` suchte nach `"name"` in ui_fields, Templates verwenden aber `"id"` – alle Felder wurden übersprungen
- **Handler-Ladepfad falsch** – Code konstruierte `templates.handlers.src.templates.handlers.usb_handler...` statt den vollständigen Pfad per `rsplit(".", 1)` zu parsen; betraf `wizard_v2.py` und `template_manager.py`
- **SyntaxWarning in `paths.py`** – Backslash im Docstring entfernt

## [0.3.11-beta] - 2026-04-08

### Fixed
- **Auto-Updater: Tägliche Prüfung** – letzte Prüfung wird in `~/.scrat-backup/last_update_check` gespeichert, kein unnötiger API-Request bei jedem Start
- **`from src import __version__` im Bundle** – try/except mit Fallback-Versionsnummer verhindert ImportError in PyInstaller-Builds

## [0.3.10-beta] - 2026-04-08

### Fixed
- **NameError QPushButton / QTableWidget / QProgressBar / QFileDialog** – fehlende Imports in `wizard_v2.py` ergänzt
- **0 Templates geladen** – Template-JSON-Dateien (`usb.json`, `nextcloud.json`, `onedrive.json`, `google_drive.json`, `dropbox.json`, `synology.json`, `qnap.json`) waren nicht im Repository – alle 7 Dateien angelegt und committed

## [0.3.9-beta] - 2026-04-08

### Fixed
- **OSError: read-only filesystem im AppImage** – `template_manager._get_system_templates_dir()` rief `mkdir()` im squashfs-Read-only-Dateisystem auf
  - Neu: `sys._MEIPASS`-basierte Pfadermittlung für Bundle-Umgebung
  - Fallback-Kette: PyInstaller-Bundle → `/usr/share/scrat-backup/templates/` → relativ zu `__file__` → `~/.scrat-backup/templates/`

## [0.3.8-beta] - 2026-04-08

### Fixed
- **Windows: App startet ohne Ausgabe** – `console=False` schluckte alle Fehler; Debug-Build bestätigte, dass App korrekt läuft sobald Import-Fehler behoben sind

## [0.3.7-beta] - 2026-04-08

### Fixed
- **LoadLibrary: Unzulässiger Zugriff (Windows DLL)** – UPX-Komprimierung löst Windows Exploit Guard / DEP-Speicherschutz aus
  - `upx=False` und `strip=False` in `scrat_backup.spec` (EXE + COLLECT) gesetzt

## [0.3.6-beta] - 2026-04-08

### Fixed
- **ModuleNotFoundError: PySide6 (Windows)** – `pyproject.toml` hat keine `[project.dependencies]`-Sektion; `pip install -e ".[dev]"` installierte keine Pakete
  - GitHub Actions: auf `pip install -r requirements.txt` umgestellt

## [0.3.5-beta] - 2026-04-08

### Fixed
- **Inno Setup: WizardImageFile nicht gefunden** – `WizModernImage-IS.bmp` existiert nicht in der CI-Inno-Setup-Version
  - `WizardImageFile=` und `WizardSmallImageFile=` Zeilen aus `installer.iss` entfernt

## [0.3.4-beta] - 2026-04-08

### Changed
- **Windows: ZIP → Installer (.exe)** – Windows-Build erstellt jetzt einen richtigen Inno Setup Installer statt eines ZIP-Archivs
  - Installiert nach `%LocalAppData%\Scrat-Backup` (kein Administratorrecht erforderlich)
  - Startmenü-Integration und optionaler Desktop-Shortcut
  - Version wird per `/DMyAppVersion=` Kommandozeilenparameter übergeben

## [0.3.3-beta] - 2026-04-08

### Added
- **Auto-Updater:** Prüft täglich auf neue Versionen via GitHub Releases API
  - `src/core/update_checker.py`: `UpdateChecker(QThread)` mit `update_available`-Signal
  - `src/gui/update_dialog.py`: Dialog mit Release-Notes, Download-Link und Direktdownload-Button
  - Plattformspezifischer Download-Link aus den Release-Assets
  - Einmalige Prüfung pro Tag (Datum in `~/.scrat-backup/last_update_check`)

## [0.3.2-beta] - 2026-04-08

### Added
- **GitHub Actions CI:** Automatische Builds bei `v*`-Tags
  - `build-windows` (windows-latest): PyInstaller → Inno Setup EXE
  - `build-linux` (ubuntu-22.04): PyInstaller → AppImage
  - Release-Assets werden automatisch hochgeladen (`softprops/action-gh-release@v2`)

## [0.3.1-beta] - 2026-04-08

### Fixed
- **PyInstaller-Optimierung:** `scrat_backup.spec` überarbeitet
  - Explizite `hidden_imports` (nur gebrauchte Module)
  - Große `excludes`-Liste (Qt6Quick, Qml, Pdf, Multimedia, Bluetooth, WebEngine, 3D)
  - `remove_qt_libs()`: filtert ungenutzle Qt-`.so`-Dateien post-Analyse
  - `optimize=1` in PYZ (entfernt Docstrings, kleinere `.pyc`)
  - Template-JSON-Dateien über `glob.glob()` in `datas` eingebunden

## [0.3.0-beta] - 2026-04-08

### Added
- **Restore-Flow im Wizard:** Neue Wizard-Seite für Wiederherstellung direkt aus dem Setup-Assistenten
  - DB-Modus: lädt automatisch aus `~/.scrat-backup/metadata.db` (vorhandene Konfiguration)
  - Verzeichnis-Modus: Backup-Ordner manuell wählen, `metadata.db` wird automatisch gesucht (für neues System)
  - Vollständige Fortschrittsanzeige mit Phase, Dateizähler und aktuellem Dateinamen
- **metadata.db auf Backup-Ziel kopieren:** Nach jedem Backup wird die Datenbank automatisch auf das Zielmedium kopiert – ermöglicht Restore auf neuem System ohne Originalrechner
- **Encryption-Page im Wizard:** Passwort-Eingabe mit Bestätigung, Live-Validierung und optionaler Keyring-Speicherung
- **System Tray funktionsfähig:** Nach dem Wizard startet Scrat-Backup im Hintergrund; Kontextmenü mit Backup starten, Wiederherstellen, Hauptfenster, Beenden
- **Passwort-Kette:** Passwort wird automatisch aus Wizard → Keyring → Dialog gelesen (kein unnötiger Dialog-Popup mehr bei gespeichertem Passwort)

### Fixed
- **Rotation löscht jetzt Backup-Dateien auf Disk:** `_rotate_old_backups()` entfernt auch die `.enc`-Dateien auf dem Backup-Medium, nicht nur die DB-Einträge
- **SFTP Host-Key-Sicherheit:** Ersetzt `AutoAddPolicy` durch `RejectPolicy` + System-Known-Hosts; klare Fehlermeldung mit Lösungsanleitung bei unbekanntem Host
- **Template-Kacheln blockieren Klick wenn nicht verfügbar:** Nicht-installierte Backends (rclone, smbclient) können nicht mehr versehentlich ausgewählt werden; Cursor wechselt zu ⊘

## [0.2.1] - 2026-02-07

### 🔥 Kritische Fixes & Remote-Upload Support

### Added
- **Remote-Upload für WebDAV/Nextcloud:** Backup wird lokal erstellt, dann zu Remote-Ziel hochgeladen (2-Step-Process)
- **Extensives Debug-Logging:** Für WebDAV-Verzeichnis-Erstellung und Upload-Prozess

### Fixed
- **KRITISCH - Remote-Backup-Upload (WebDAV/Nextcloud):**
  - Fortschrittsfenster blieb nicht während Upload offen
  - WebDAV mkdir benötigt führenden Slash für Remote-Pfade
  - WebDAV-Verzeichnis-Erstellung von rekursiv auf iterativ umgestellt
  - `upload_file()` erwartet Path-Objekt, nicht String
  - Nextcloud-Upload: `dest_type 'nextcloud'` wird jetzt erkannt
  - `BackupResult` hat kein `backup_path` Attribut - Pfad wird jetzt konstruiert
  - Path-Fehler bei Remote-Backup (str vs Path) behoben
- **Einrückungsfehler in main.py:** Syntax-Fehler behoben

## [0.2.0] - 2026-02-06

### 🎉 Produktionsreife mit Performance-Fixes!

### Changed
- **Wizard ist IMMER Einstiegspunkt:** Wizard startet bei jedem Programmstart (nicht nur beim ersten Mal)
  - Im Wizard wird zwischen Normal-Modus und Experten-Modus gewählt
  - MainWindow öffnet sich nur bei Experten-Modus
  - Vereinfacht User-Flow und macht Settings-Änderungen zugänglicher

### Added
- **SchedulePage im Wizard:** Zeitplan-Konfiguration (täglich/wöchentlich/monatlich/beim Start)
- **Edit-Modus vorbefüllt:** SourceSelectionPage lädt vorhandene Quellen aus Config
- **Debug-Tool:** `debug_usb.sh` für USB-Laufwerks-Diagnose unter Linux
- **Chunked Encryption:** Dateien werden in 64MB-Chunks verschlüsselt (kein OOM mehr bei großen Dateien)
- **Extensives Debug-Logging:** Für Quellen-Matching und Edit-Modus Troubleshooting

### Fixed
- **KRITISCH - OOM-Kill bei großen Dateien:** Mehrere Fixes implementiert
  - Split-Size von 500MB → 128MB reduziert (weniger RAM pro Archiv)
  - Chunked Encryption implementiert (64MB Chunks statt gesamte Datei in RAM)
  - encryptor.py: `plaintext = f_in.read()` durch Chunk-basiertes Lesen ersetzt
- **Config-Duplikate:** Bei "Edit" wurden Quellen/Ziele angehängt statt ersetzt
  - Explizites `save()` nach Löschen der Arrays verhindert Duplikate
- **Edit-Modus lädt keine Quellen:** Mehrere Fixes
  - `_prefilled` Flag entfernt (verhinderte wiederholtes Laden)
  - `wizard.field("start_action")` gab String `'None'` zurück → Direkter Zugriff auf `start_page.selected_action`
  - Checkboxen werden IMMER zurückgesetzt bei `initializePage()`
  - Pfad-Normalisierung mit `Path.resolve()` für korrektes Matching
- **Schnellauswahl-Duplikate:** Desktop und Dokumente entfernt (sind bereits Checkboxen)
- **py7zr Kompatibilität:** `multithread`-Parameter mit Try-Except für ältere Versionen
- **Windows:** SchedulePage wird jetzt korrekt angezeigt (nextId + setFinalPage Fix)
- **Windows:** Nach Wizard-Abschluss öffnet sich nicht mehr automatisch das MainWindow
- **Linux:** USB-Laufwerks-Erkennung mit robusten Username-Fallbacks ($USER, getpass, pwd)
- **Linux:** Externe USB-Festplatten in /media werden jetzt erkannt (removable=0 akzeptiert)
- **Linux:** Qt6 XCB-Dependencies in Dokumentation (libxcb-cursor0, etc.)
- **MainWindow:** closeEvent beendet Programm korrekt wenn kein Tray läuft
- **QProgressDialog:** Leerer Abbrechen-Button entfernt
- **SystemTray:** is_visible() statt isVisible() (AttributeError behoben)

### Performance
- **Kompression deaktiviert:** FILTER_COPY statt LZMA2 (100x schneller)
  - py7zr war extrem langsam (KB/30s statt MB/s)
  - Kompression-Level auf 1 reduziert (war zwischenzeitlich, dann ganz deaktiviert)
  - Dateien werden nur archiviert + verschlüsselt, nicht komprimiert
  - Datenrate: 128-200 MB/s (vorher: KB pro 30 Sekunden)
- **Multi-Threading:** py7zr mit `multithread=True` (Fallback für alte Versionen)

## [0.2.0-beta] - 2025-12-15

### 🎉 Beta-Release!

Erste öffentliche Testversion von Scrat-Backup mit vollständigem Scheduler und Packaging.

### Added
#### Phase 10: Scheduler & Automatisierung
- **Scheduler-Worker (Background QThread):**
  - Läuft im Hintergrund und prüft alle 60 Sekunden auf fällige Backups
  - Automatisches Triggern von geplanten Backups
  - Pause/Resume-Funktionalität
  - Graceful Shutdown beim Beenden
- **Missed-Backup-Detection:**
  - Erkennt wenn System lange ausgeschaltet war
  - Identifiziert verpasste Backups
  - User-Dialog zum Nachholen oder Überspringen
  - Automatische Neuberechnung von next_run
- **"Nächster Lauf"-Anzeige:**
  - Im Settings-Tab für jeden Zeitplan sichtbar
  - Deutsches Datumsformat (DD.MM.YYYY HH:MM)
  - Unterscheidet reguläre Zeitpläne vs. System-Events
  - Live-Updates bei Änderungen
- **Scheduler-Tests:**
  - 16 Tests für Scheduler-Klasse
  - 6 Tests für SchedulerWorker (3 geskippt als zu fragil)
  - Coverage: scheduler.py 68%, scheduler_worker.py 47%

#### Phase 12: Packaging & Distribution
- **PyInstaller Build-System:**
  - `.spec`-Konfiguration für Windows-Executable
  - Automatisches Build-Script (`build_exe.py`)
  - One-Directory Build (~200 MB)
  - Icon-Integration
  - Hidden imports für alle Dependencies
- **Inno Setup Installer:**
  - Professioneller Windows-Installer (`installer.iss`)
  - Startmenü-Integration
  - Desktop-Icon (optional)
  - Automatische Deinstallation alter Versionen
  - Deutsche und englische Meldungen
- **Dokumentation:**
  - BUILD.md - Umfassende Build-Anleitung
  - RELEASE_NOTES.md - Release-Informationen
  - docs/INSTALL.txt - Installations-Info für Installer
  - Aktualisiertes README.md für Beta-Release

### Changed
- README.md auf Beta-Status aktualisiert
- Versionsnummer von 0.1.0-dev auf 0.2.0-beta erhöht
- Status-Badges aktualisiert
- Test-Count von 121 auf 143 erhöht

### Fixed
- Scheduler-Integration in MainWindow
- Settings-Tab Update-Logik für Schedule-Details
- Icon-Pfade in PyInstaller-Konfiguration

## [0.1.0-dev] - 2025-12-01

### Phase 11: Polishing abgeschlossen

#### Added
- **Passwort-Management:**
  - Windows Credential Manager Integration
  - Sichere Passwort-Speicherung
  - Passwort-Dialog mit Stärke-Anzeige
  - "Passwort speichern"-Option

- **UI-Verbesserungen:**
  - Backup-Tab: Quellen/Ziele-Verwaltung überarbeitet
  - Restore-Tab: Backup-Details-Ansicht verbessert
  - Settings-Tab: Input-Validierung für alle Felder
  - System Tray: Notifications für Backup-Status

- **Setup-Wizard Überarbeitung:**
  - Komplett auf Deutsch
  - Automatische Laufwerk-Erkennung
  - Alle 5 Storage-Backends integriert
  - Persönliche Ordner (Dokumente, Bilder, etc.)
  - Verbesserte Usability

#### Fixed
- Input-Validierung in allen Dialogen
- Error-Handling bei fehlgeschlagenen Backups
- Memory-Leaks in Progress-Tracking
- Edge-Cases in Restore-Engine

### Phase 10: Scheduler (teilweise)

#### Added
- `scheduler.py` - Zeitplan-Logik
- `schedule_dialog.py` - Schedule-Dialog
- Schedule-Verwaltung im Settings-Tab
- Config-Persistierung für Zeitpläne
- Windows Task Scheduler Integration (Startup/Shutdown)
- `system_tray.py` - System Tray Integration

## [0.0.1-alpha] - 2025-11-27

### Phase 1-9: Grundfunktionen

#### Added
- **Core-Module:**
  - Backup-Engine (Full & Incremental)
  - Restore-Engine
  - AES-256-GCM Verschlüsselung
  - 7z Komprimierung
  - SQLite Metadaten-Verwaltung
  - Config-Manager

- **Storage-Backends:**
  - USB / Lokale Laufwerke
  - SFTP (SSH)
  - WebDAV
  - Rclone (40+ Cloud-Provider)
  - SMB/CIFS

- **GUI:**
  - Hauptfenster (PyQt6)
  - Backup-Tab
  - Restore-Tab
  - Settings-Tab
  - Logs-Tab
  - Info-Tab

- **Testing:**
  - 121 Core-Tests
  - >80% Coverage
  - pytest, pytest-qt, pytest-cov

---

## Versions-Schema

Wir folgen [Semantic Versioning](https://semver.org/lang/de/):

- **Major (X.0.0):** Breaking Changes, große Änderungen
- **Minor (0.X.0):** Neue Features, abwärtskompatibel
- **Patch (0.0.X):** Bugfixes, kleine Änderungen
- **Suffix:**
  - `-alpha`: Frühe Entwicklung, instabil
  - `-beta`: Feature-complete, Testing-Phase
  - `-rc`: Release Candidate, kurz vor Release
  - (kein Suffix): Stabile Release-Version

---

## Links

- [Releases](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases)
- [Issues](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)
- [Discussions](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions)

[Unreleased]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.11-beta...HEAD
[0.3.11-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.10-beta...v0.3.11-beta
[0.3.10-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.9-beta...v0.3.10-beta
[0.3.9-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.8-beta...v0.3.9-beta
[0.3.8-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.7-beta...v0.3.8-beta
[0.3.7-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.6-beta...v0.3.7-beta
[0.3.6-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.5-beta...v0.3.6-beta
[0.3.5-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.4-beta...v0.3.5-beta
[0.3.4-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.3-beta...v0.3.4-beta
[0.3.3-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.2-beta...v0.3.3-beta
[0.3.2-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.1-beta...v0.3.2-beta
[0.3.1-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.3.0-beta...v0.3.1-beta
[0.3.0-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/tag/v0.3.0-beta
[0.2.0-beta]: https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/tag/v0.2.0-beta
[0.1.0-dev]: https://github.com/nicolettas-muggelbude/Scrat-Backup/compare/v0.0.1-alpha...v0.1.0-dev
[0.0.1-alpha]: https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/tag/v0.0.1-alpha
