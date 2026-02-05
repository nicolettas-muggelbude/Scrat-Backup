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
- **Backup nach Wizard:** `start_backup_after_wizard()` in `main.py` – Fortschrittsanzeige (QProgressDialog, nicht schließbar bis fertig), Thread-sichere Fortschritts-Updates
- **App-Logo:** Eichel-Icon auf allen Fenstern (QApplication-Level `setWindowIcon` in `main.py` + `run_wizard.py`)
- **TemplateCard-Kacheln:** QFrame-basierte Kacheln mit 24px-Icons, Hover/Check-Styles, rahmenlos (ersetzt QPushButton)

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
sudo apt install python3-keyring libsecret-1-0 smbclient cron

# Python (Linux-spezifisch)
pip install secretstorage python-notify2 pyxdg
```
