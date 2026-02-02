# Scrat-Backup - Entwicklungsplan

## Projektübersicht

Scrat-Backup ist ein benutzerfreundliches Backup-Tool mit verschlüsselten, komprimierten Backups.

**Vision:** Wizard-zentrierte Architektur mit Template-System für verschiedene Backup-Ziele.

---

## Architektur-Konzept

### Zwei Modi:

```
┌─────────────────────────────────────────────────────────────┐
│                     Desktop-Starter                          │
│                  scrat-backup-wizard                         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   SetupWizard (Hauptprogramm)                │
│                                                              │
│  Seite 1: [Normal-Modus] ←→ [Power-User-Modus]             │
│              ↓                        ↓                      │
│      Template-basiert            MainWindow                  │
│      (USB, OneDrive, ...)       + Template-Manager           │
│              ↓                                               │
│      Seite 2-6: Konfiguration                               │
│              ↓                                               │
│      Letzte Seite:                                          │
│      [Fertig] [Backup jetzt starten]                        │
│              ↓                                               │
└──────────────┬──────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│                    System Tray                               │
│  • Wizard erneut öffnen (für Änderungen)                    │
│  • Backup starten                                            │
│  • Hauptfenster anzeigen (Power-User)                       │
└─────────────────────────────────────────────────────────────┘
```

### Normal-User-Modus:
- Template-basierte Konfiguration
- Vorlagen für: USB, OneDrive, Google Drive, Nextcloud, Synology, QNAP, ...
- Einfache, geführte Einrichtung
- Nach Fertigstellung: Tray startet

### Power-User-Modus:
- Öffnet MainWindow zusätzlich zum Wizard
- Zugriff auf alle erweiterten Funktionen
- Kann Templates nutzen UND eigene Konfigurationen erstellen
- Template-Manager zum Erstellen eigener Templates

---

## Implementierungsplan

### Phase 1: Template-System (Basis)

**Ziel:** Grundlage für Template-basierte Konfiguration schaffen

#### 1.1 TemplateManager (`src/core/template_manager.py`)

```python
class TemplateManager:
    """Verwaltet Backup-Ziel-Templates"""

    def __init__(self):
        self.system_templates_dir = Path("/usr/share/scrat-backup/templates/")
        self.user_templates_dir = Path.home() / ".scrat-backup/templates/"

    def get_available_templates(self) -> List[Template]:
        """Lädt alle verfügbaren Templates und prüft Verfügbarkeit"""

    def get_template_by_id(self, template_id: str) -> Template:
        """Lädt ein spezifisches Template"""

    def create_template(self, template_data: dict) -> Template:
        """Erstellt ein neues User-Template"""

    def validate_template(self, template: Template) -> bool:
        """Validiert Template-Struktur"""
```

#### 1.2 Template-Schema (JSON)

```json
{
  "id": "synology",
  "version": "1.0",
  "display_name": "Synology NAS",
  "icon": "synology.png",
  "description": "Backup auf Synology DiskStation",
  "category": "nas",
  "storage_type": "smb",
  "handler": "synology_handler",

  "ui_fields": [
    {
      "name": "host",
      "type": "text",
      "label": "Synology IP/Hostname",
      "placeholder": "192.168.1.100 oder nas.local",
      "required": true,
      "validation": "^[a-zA-Z0-9.-]+$"
    },
    {
      "name": "share",
      "type": "dropdown",
      "label": "Freigabe",
      "options": "dynamic",
      "options_source": "scan_shares",
      "required": true
    },
    {
      "name": "user",
      "type": "text",
      "label": "Benutzername",
      "required": true
    },
    {
      "name": "password",
      "type": "password",
      "label": "Passwort",
      "required": true,
      "store": "keyring"
    },
    {
      "name": "path",
      "type": "text",
      "label": "Unterordner",
      "placeholder": "/scrat-backups",
      "default": "/scrat-backups"
    }
  ],

  "config_mapping": {
    "type": "smb",
    "server": "${host}",
    "port": 445,
    "share": "${share}",
    "user": "${user}",
    "password": "${password}",
    "path": "${path}"
  },

  "availability_check": {
    "type": "dependency",
    "dependencies": ["smbclient"]
  }
}
```

#### 1.3 Template-Handler (`src/templates/handlers/`)

**Base Handler:**
```python
class TemplateHandler(ABC):
    """Basis-Klasse für Template-Handler"""

    @abstractmethod
    def check_availability(self) -> bool:
        """Prüft ob Template verfügbar ist"""

    @abstractmethod
    def setup(self, config: dict) -> dict:
        """Führt Template-spezifisches Setup durch"""

    @abstractmethod
    def validate(self, config: dict) -> tuple[bool, str]:
        """Validiert Konfiguration"""
```

**Beispiel: USB Handler** (`usb_handler.py`):
```python
class UsbHandler(TemplateHandler):
    def check_availability(self) -> bool:
        """Prüft ob USB-Geräte verfügbar sind"""
        return len(self.detect_usb_drives()) > 0

    def detect_usb_drives(self) -> List[dict]:
        """Erkennt USB-Laufwerke"""
        # Windows: GetDriveTypeW == 2 (Removable)
        # Linux: /sys/block/*/removable == 1

    def setup(self, config: dict) -> dict:
        """Erstellt Backup-Ordner auf USB"""
```

**Beispiel: OneDrive Handler** (`onedrive_handler.py`):
```python
class OneDriveHandler(TemplateHandler):
    def check_availability(self) -> bool:
        """Prüft ob rclone installiert ist"""
        return shutil.which("rclone") is not None

    def check_authentication(self) -> bool:
        """Prüft ob OneDrive bereits authentifiziert ist"""
        # rclone listremotes

    def setup(self, config: dict) -> dict:
        """Führt OAuth-Flow durch und konfiguriert rclone"""
        # rclone config create onedrive onedrive

    def install_rclone(self):
        """Installiert rclone falls nicht vorhanden"""
```

**Beispiel: Synology Handler** (`synology_handler.py`):
```python
class SynologyHandler(TemplateHandler):
    def scan_shares(self, host: str, user: str, password: str) -> List[str]:
        """Scannt SMB-Freigaben auf Synology"""
        # smbclient -L //host -U user

    def validate(self, config: dict) -> tuple[bool, str]:
        """Testet SMB-Verbindung"""
        # smbclient //server/share -U user -c "ls"
```

#### 1.4 Initiale Templates

- ✅ **usb** - USB-Laufwerk / externe Festplatte
- ✅ **onedrive** - Microsoft OneDrive (rclone)
- ✅ **synology** - Synology NAS (SMB)
- **google_drive** - Google Drive (rclone)
- **nextcloud** - Nextcloud (WebDAV)
- **qnap** - QNAP NAS (SMB)
- **dropbox** - Dropbox (rclone)
- **sftp** - SFTP-Server

---

### Phase 2: Wizard-Umbau

**Ziel:** Wizard auf Template-System umstellen

#### 2.1 Neue ModePage (Seite 1)

```
┌─────────────────────────────────────────────────────┐
│  Willkommen bei Scrat-Backup!                       │
│                                                      │
│  [Eichel-Icon]                                      │
│                                                      │
│  Wie möchtest du Scrat-Backup nutzen?               │
│                                                      │
│  ┌────────────────────────┐  ┌──────────────────┐  │
│  │   🐿️ Einfacher Modus   │  │  ⚙️ Experten-   │  │
│  │                        │  │     Modus        │  │
│  │  Geführte Einrichtung  │  │                  │  │
│  │  mit Vorlagen          │  │  Volle Kontrolle │  │
│  │                        │  │  & Anpassungen   │  │
│  │  [Empfohlen]           │  │                  │  │
│  └────────────────────────┘  └──────────────────┘  │
│                                                      │
│                            [Weiter] [Abbrechen]     │
└─────────────────────────────────────────────────────┘
```

**Implementation:**
```python
class ModePage(QWizardPage):
    def __init__(self):
        # Radio-Buttons oder Große Klick-Karten
        self.normal_mode_btn = ...
        self.expert_mode_btn = ...

        # Bei Experten-Modus: MainWindow öffnen
        self.expert_mode_btn.clicked.connect(self._open_expert_mode)

    def _open_expert_mode(self):
        """Öffnet MainWindow für Power-User"""
        from gui.main_window import MainWindow
        self.expert_window = MainWindow()
        self.expert_window.show()
```

#### 2.2 Template-basierte DestinationPage

**Kategorisierte Ansicht:**
```
┌──────────────────────────────────────────────────────┐
│  Wo sollen die Backups gespeichert werden?           │
├──────────────────────────────────────────────────────┤
│  📁 Lokal                                            │
│  ┌─────────────┐                                     │
│  │ 💾 USB      │                                     │
│  └─────────────┘                                     │
│                                                       │
│  ☁️ Cloud                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ OneDrive │ │  Google  │ │ Dropbox  │            │
│  │          │ │  Drive   │ │          │            │
│  └──────────┘ └──────────┘ └──────────┘            │
│  ┌──────────┐                                       │
│  │Nextcloud │                                       │
│  └──────────┘                                       │
│                                                       │
│  🖥️ NAS                                              │
│  ┌──────────┐ ┌──────────┐                         │
│  │Synology  │ │  QNAP    │                         │
│  └──────────┘ └──────────┘                         │
│                                                       │
│  🌐 Server                                           │
│  ┌──────────┐ ┌──────────┐                         │
│  │  SFTP    │ │ WebDAV   │                         │
│  └──────────┘ └──────────┘                         │
└──────────────────────────────────────────────────────┘
```

**Nach Template-Auswahl:**
```
┌──────────────────────────────────────────────────────┐
│  Synology NAS einrichten                              │
│                                                       │
│  Backup auf Synology DiskStation                     │
├──────────────────────────────────────────────────────┤
│  Synology IP/Hostname:                               │
│  [192.168.1.100        ]                             │
│                                                       │
│  Freigabe:                                           │
│  [Freigaben suchen...  ▼]  [🔍 Scannen]             │
│                                                       │
│  Benutzername:                                       │
│  [admin                ]                             │
│                                                       │
│  Passwort:                                           │
│  [••••••••••••••••••••]                             │
│                                                       │
│  Unterordner:                                        │
│  [/scrat-backups       ]                             │
│                                                       │
│  [✅ Verbindung testen]                              │
│                                                       │
│                      [← Zurück] [Weiter →]          │
└──────────────────────────────────────────────────────┘
```

**Implementation:**
```python
class TemplateDestinationPage(QWizardPage):
    def __init__(self):
        self.template_manager = TemplateManager()
        self.selected_template = None

        # Template-Auswahl (kategorisiert)
        self.template_selector = TemplateSelectorWidget()

        # Dynamisches Formular für Template-Felder
        self.template_form = DynamicTemplateForm()

    def _on_template_selected(self, template: Template):
        """Zeigt Template-spezifisches Formular"""
        self.selected_template = template
        self.template_form.build_form(template)

class TemplateSelectorWidget(QWidget):
    """Grid mit Template-Kacheln, kategorisiert"""

    def __init__(self):
        # Kategorien: Lokal, Cloud, NAS, Server
        self.categories = {}

    def load_templates(self):
        """Lädt verfügbare Templates vom TemplateManager"""
        templates = self.template_manager.get_available_templates()
        # Kategorisieren und anzeigen

class DynamicTemplateForm(QWidget):
    """Erstellt Formular basierend auf Template-Definition"""

    def build_form(self, template: Template):
        """Baut UI-Felder aus template.ui_fields"""
        for field in template.ui_fields:
            if field.type == "text":
                self._add_text_field(field)
            elif field.type == "dropdown":
                self._add_dropdown_field(field)
            elif field.type == "password":
                self._add_password_field(field)
```

#### 2.3 FinishPage mit Tray-Start

```
┌──────────────────────────────────────────────────────┐
│  Einrichtung abgeschlossen! 🎉                        │
├──────────────────────────────────────────────────────┤
│  Scrat-Backup ist jetzt konfiguriert und bereit.    │
│                                                       │
│  [Zusammenfassung wie bisher...]                     │
│                                                       │
│  ┌────────────────────────────────────────────────┐ │
│  │ ☐ Backup jetzt starten                         │ │
│  │                                                 │ │
│  │   Führt sofort ein erstes Backup durch         │ │
│  └────────────────────────────────────────────────┘ │
│                                                       │
│  ☑️ Scrat-Backup im Hintergrund starten (Tray)      │
│                                                       │
│                              [Fertig]                │
└──────────────────────────────────────────────────────┘
```

**Implementation:**
```python
class FinishPage(QWizardPage):
    def __init__(self):
        # Bestehende Zusammenfassung
        self.summary_label = QLabel()

        # NEU: Backup jetzt starten
        self.start_backup_now = QCheckBox("Backup jetzt starten")

        # NEU: Tray starten (standardmäßig aktiviert)
        self.start_tray = QCheckBox("Scrat-Backup im Hintergrund starten (Tray)")
        self.start_tray.setChecked(True)

    def validatePage(self) -> bool:
        """Bei Finish: Tray starten + optional Backup"""
        if self.start_tray.isChecked():
            self._start_tray()

        if self.start_backup_now.isChecked():
            self._start_initial_backup()

        return True

    def _start_tray(self):
        """Startet System Tray"""
        from gui.system_tray import SystemTray
        # Tray in Hintergrund-Thread starten

    def _start_initial_backup(self):
        """Startet erstes Backup"""
        # BackupEngine mit Wizard-Config starten
```

#### 2.4 Wizard-Seitenfolge

**Normal-Modus:**
1. ModePage - Normal/Experten-Auswahl
2. SourcesPage - Backup-Quellen (wie bisher)
3. TemplateDestinationPage - Template-Auswahl + Konfiguration
4. EncryptionPage - Verschlüsselung (wie bisher)
5. SchedulePage - Zeitplan (wie bisher)
6. FinishPage - Zusammenfassung + Tray-Start + Backup-Option

**Experten-Modus:**
- ModePage öffnet MainWindow
- Wizard kann trotzdem durchlaufen werden
- Beide Oberflächen parallel nutzbar

---

### Phase 3: Integration

**Ziel:** Nahtlose Integration in bestehendes System

#### 3.1 main.py Anpassung

**Aktuell:**
```python
def main():
    if check_first_run():
        wizard = SetupWizard()
        wizard.exec()

    window = MainWindow()
    window.show()
```

**Neu:**
```python
def main():
    # Wizard ist IMMER Einstiegspunkt
    wizard = SetupWizard()
    result = wizard.exec()

    if result == QDialog.Rejected:
        # User hat abgebrochen
        return

    # Tray wurde bereits im Wizard gestartet (falls aktiviert)
    # Hauptprogramm nur im Experten-Modus oder bei explizitem Aufruf
```

**Oder: Tray-zentriert:**
```python
def main():
    # Check ob bereits konfiguriert
    if ConfigManager().is_configured():
        # Starte Tray
        start_tray()
    else:
        # Erste Einrichtung: Wizard
        wizard = SetupWizard()
        wizard.exec()
```

#### 3.2 Tray-Menü Erweiterung

**Aktuelles Tray-Menü:**
```
Hauptfenster anzeigen
─────────────────
Backup starten
Wiederherstellen
─────────────────
Einstellungen
─────────────────
Beenden
```

**Neues Tray-Menü:**
```
Assistent öffnen           [NEU]
Hauptfenster anzeigen
─────────────────
Backup starten
Wiederherstellen
─────────────────
Einstellungen
─────────────────
Beenden
```

**Implementation:**
```python
class SystemTray:
    def _create_menu(self):
        # NEU: Wizard öffnen
        wizard_action = QAction("Assistent öffnen", self)
        wizard_action.triggered.connect(self._open_wizard)
        menu.addAction(wizard_action)

        # Bestehende Actions...

    def _open_wizard(self):
        """Öffnet Wizard für Änderungen"""
        from gui.wizard import SetupWizard
        wizard = SetupWizard()
        wizard.exec()
```

#### 3.3 MainWindow: Template-Manager-Tab

**Neuer Tab im MainWindow:**
```
[Backup] [Restore] [Settings] [Logs] [Info] [Templates]  ← NEU
```

**Template-Manager UI:**
```
┌──────────────────────────────────────────────────────┐
│  Template-Manager                                     │
├──────────────────────────────────────────────────────┤
│  System-Templates:                                   │
│  ┌──────────────────────────────────────────────┐   │
│  │ • USB-Laufwerk          [Ansehen]            │   │
│  │ • OneDrive              [Ansehen]            │   │
│  │ • Google Drive          [Ansehen]            │   │
│  │ • Synology NAS          [Ansehen]            │   │
│  │ ...                                          │   │
│  └──────────────────────────────────────────────┘   │
│                                                       │
│  Eigene Templates:                                   │
│  ┌──────────────────────────────────────────────┐   │
│  │ • Mein Custom Server    [Bearbeiten] [Löschen] │
│  │ • Firma Backup          [Bearbeiten] [Löschen] │
│  └──────────────────────────────────────────────┘   │
│                                                       │
│  [+ Neues Template erstellen]                        │
└──────────────────────────────────────────────────────┘
```

**Implementation:**
```python
class TemplateManagerTab(QWidget):
    def __init__(self):
        self.template_manager = TemplateManager()

        # Listen für System- und User-Templates
        self.system_templates_list = QListWidget()
        self.user_templates_list = QListWidget()

        # Buttons
        self.create_btn = QPushButton("+ Neues Template erstellen")
        self.create_btn.clicked.connect(self._create_template)

    def _create_template(self):
        """Öffnet Template-Editor-Dialog"""
        dialog = TemplateEditorDialog()
        if dialog.exec():
            template_data = dialog.get_template_data()
            self.template_manager.create_template(template_data)

class TemplateEditorDialog(QDialog):
    """Dialog zum Erstellen/Bearbeiten von Templates"""
    # JSON-Editor oder Form für Template-Felder
```

#### 3.4 Desktop-Starter

**scrat-backup-wizard.desktop:**
```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Scrat-Backup Assistent
Name[de]=Scrat-Backup Assistent
GenericName=Backup Configuration
GenericName[de]=Backup-Konfiguration
Comment=Configure Scrat-Backup
Comment[de]=Scrat-Backup konfigurieren
Exec=scrat-backup --wizard
Icon=scrat-backup
Terminal=false
Categories=Utility;Archiving;
Keywords=backup;restore;archive;
```

**scrat-backup-tray.desktop:**
```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Scrat-Backup
Name[de]=Scrat-Backup
GenericName=Backup Tool
Comment=Automated backup solution
Comment[de]=Automatisierte Backup-Lösung
Exec=scrat-backup --tray
Icon=scrat-backup
Terminal=false
Categories=Utility;Archiving;
Keywords=backup;restore;archive;
X-GNOME-Autostart-enabled=true
```

**CLI-Argumente in main.py:**
```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wizard", action="store_true", help="Öffne Setup-Wizard")
    parser.add_argument("--tray", action="store_true", help="Starte nur Tray")
    args = parser.parse_args()

    if args.wizard:
        wizard = SetupWizard()
        wizard.exec()
    elif args.tray:
        start_tray()
    else:
        # Standard: MainWindow
        window = MainWindow()
        window.show()
```

---

### Phase 4: Polish & Finalisierung

#### 4.1 Template-Kategorisierung

**Kategorien:**
- 📁 **Lokal** - USB, Externe Festplatten
- ☁️ **Cloud** - OneDrive, Google Drive, Dropbox, iCloud
- 🖥️ **NAS** - Synology, QNAP, FreeNAS, TrueNAS
- 🌐 **Server** - SFTP, WebDAV, SMB, rsync

**Filterung:**
```python
class TemplateSelectorWidget:
    def filter_by_category(self, category: str):
        """Zeigt nur Templates einer Kategorie"""
```

#### 4.2 Template-Icons

**Icon-Set erstellen:**
- `assets/templates/usb.svg`
- `assets/templates/onedrive.svg`
- `assets/templates/google_drive.svg`
- `assets/templates/synology.svg`
- ...

**Fallback:** Generic Icons für Kategorien

#### 4.3 Lokalisierung

**Strings externalisieren:**
```python
# i18n/de.json
{
  "wizard.mode.title": "Wie möchtest du Scrat-Backup nutzen?",
  "wizard.mode.normal": "Einfacher Modus",
  "wizard.mode.expert": "Experten-Modus",
  "template.category.local": "Lokal",
  "template.category.cloud": "Cloud",
  ...
}
```

#### 4.4 Tests

**Unit-Tests:**
- `test_template_manager.py` - Template-Laden, Validierung
- `test_template_handlers.py` - Handler-Funktionalität
- `test_wizard_flow.py` - Wizard-Durchlauf

**Integration-Tests:**
- Template-basierte Backup-Erstellung
- Tray-Integration
- Wizard → Tray → Backup Flow

---

## Offene Fragen & Entscheidungen

### Template-Verfügbarkeit

**Frage:** Wie strikt filtern wir Templates?

**Optionen:**
1. **Strikt:** Nur verfügbare Templates anzeigen
   - USB nur wenn USB-Gerät erkannt
   - OneDrive nur wenn rclone installiert
   - Pro: Keine verwirrenden Optionen
   - Contra: User kann nichts vorbereiten

2. **Permissiv:** Alle Templates anzeigen, aber Warnung bei fehlenden Requirements
   - "OneDrive benötigt rclone (nicht installiert) - [Installieren]"
   - Pro: User kann alles konfigurieren
   - Contra: Eventuell verwirrend

**Empfehlung:** Permissiv mit klaren Hinweisen + Auto-Installation

### Wizard nach Ersteinrichtung

**Frage:** Was passiert beim zweiten Wizard-Start?

**Optionen:**
1. Wizard startet normal, zeigt aber aktuelle Config als Defaults
2. Wizard zeigt Übersichtsseite: "Bereits konfiguriert - [Ändern] [Neues Ziel hinzufügen]"
3. Wizard überspringt WelcomePage, startet bei Änderungsauswahl

**Empfehlung:** Option 2 - Übersichtsseite mit Änderungs-Optionen

### Multi-Destination Support

**Frage:** Kann User mehrere Backup-Ziele einrichten?

**Aktuell:** Ein Ziel pro Wizard-Durchlauf

**Zukünftig:**
- "Weiteres Ziel hinzufügen" Button auf FinishPage
- Templates können kombiniert werden (USB + Cloud)

---

## Technische Details

### Template-Loading Performance

**Problem:** Viele Templates laden kann langsam sein

**Lösung:**
```python
class TemplateManager:
    def __init__(self):
        self._cache = {}
        self._last_scan = None

    def get_available_templates(self, force_refresh=False):
        if force_refresh or self._cache_expired():
            self._scan_templates()
        return self._cache.values()
```

### Template-Handler Plugin-System

**Zukünftig:** Handler als Plugins
```
~/.scrat-backup/plugins/
  ├── my_custom_handler.py
  └── template.json
```

Dynamisches Laden:
```python
class TemplateManager:
    def _load_handlers(self):
        """Lädt Handler aus plugins/ Verzeichnis"""
        for plugin_dir in self.plugin_dirs:
            ...
```

---

## Migrationspfad

### Für bestehende Nutzer

**Upgrade von v0.1.0 → v1.0.0 (Template-System):**

1. **Config-Migration:**
```python
def migrate_config_to_templates():
    """Konvertiert alte Storage-Config zu Template-basiert"""
    old_config = ConfigManager().get_section("destinations")

    for dest in old_config:
        if dest["type"] == "usb":
            # Matche zu USB-Template
            new_dest = {
                "template_id": "usb",
                "template_config": {...}
            }
```

2. **Wizard-Skip:**
   - Beim ersten Start nach Update: "Config erkannt - [Behalten] [Neu konfigurieren]"

---

## Zeitplan

### Milestone 1: Template-System (1-2 Wochen)
- TemplateManager
- 3 initiale Templates (USB, OneDrive, Synology)
- Handler-Implementierung

### Milestone 2: Wizard-Umbau (1 Woche)
- ModePage
- TemplateDestinationPage
- FinishPage mit Tray-Start

### Milestone 3: Integration (1 Woche)
- Tray-Menü erweitern
- Template-Manager-Tab
- Desktop-Starter

### Milestone 4: Polish (1 Woche)
- Icons
- Lokalisierung
- Tests
- Dokumentation

**Gesamt: ca. 4-5 Wochen**

---

## Notizen & Ideen

### Template-Marketplace (Zukunft)
- Online-Repository für Community-Templates
- "Template aus URL importieren"
- Template-Sharing

### Template-Wizard (Zukunft)
- "Erstelle Template aus bestehender Config"
- Template-Generator für Power-User

### Erweiterte Template-Features
- Mehrsprachige Display-Namen
- Template-Versioning & Updates
- Template-Dependencies (OneDrive benötigt rclone)
- Template-Testing (Dry-Run)

---

## Linux-Kompatibilität

### Strategie: EINE Code-Basis mit plattformspezifischen Handlern

**Entscheidung:** Keine separate Linux-Version, sondern plattformabstrahierte Implementierung.

### ✅ Bereits plattformunabhängig:

1. **PySide6 UI** - Qt läuft auf Windows, Linux, macOS
2. **Backup-Engine** - Verschlüsselung (AES-256), Kompression (7z)
3. **Storage-Backends** - SFTP, WebDAV, Rclone, SMB
4. **Config-System** - JSON-basiert, `pathlib.Path` für Pfade
5. **Credential Storage** - `keyring` Bibliothek (Windows: DPAPI, Linux: SecretService)
6. **System Tray** - Qt-Tray funktioniert überall

### ⚠️ Plattformspezifische Komponenten:

#### 1. **Laufwerks-Erkennung** ✅ Bereits abstrahiert
```python
# src/gui/wizard.py:432
if platform.system() == "Windows":
    # Windows: C:, D:, E: via GetDriveTypeW
else:
    # Linux: /media/*, /mnt/*
```

#### 2. **Task Scheduler / Cron** ✅ NEU: `platform_scheduler.py`
```python
# src/core/platform_scheduler.py
scheduler = get_platform_scheduler()  # Factory
if scheduler:
    scheduler.register_task("backup", "startup", ...)
```

**Implementiert:**
- `WindowsTaskScheduler` - schtasks.exe
- `LinuxCronScheduler` - crontab
- `MacOSLaunchdScheduler` - launchd (Placeholder)

#### 3. **Autostart** ✅ NEU: `autostart.py`
```python
# src/core/autostart.py
manager = AutostartManager()
manager.enable_autostart()  # Plattformunabhängig
```

**Implementiert:**
- Windows: Registry `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- Linux: `.desktop` in `~/.config/autostart/`
- macOS: LaunchAgent in `~/Library/LaunchAgents/`

#### 4. **Standard-Ordner** - Benötigt Anpassung
**Windows:**
```python
Path.home() / "Documents"
Path.home() / "Pictures"
Path.home() / "Music"
```

**Linux:**
```python
# XDG User Directories (via xdg-user-dir)
subprocess.run(["xdg-user-dir", "DOCUMENTS"], capture_output=True).stdout.strip()
# Oder: ~/.config/user-dirs.dirs parsen
```

**Lösung:**
```python
def get_user_folder(folder_type: str) -> Path:
    """Plattformunabhängige User-Ordner"""
    if platform.system() == "Windows":
        return Path.home() / WINDOWS_FOLDERS[folder_type]
    elif platform.system() == "Linux":
        return _get_xdg_folder(folder_type)
    else:
        return Path.home() / folder_type.lower()
```

#### 5. **Benachrichtigungen**
- Windows: Toast Notifications (Windows 10+)
- Linux: D-Bus Notifications (notify-send, python-notify2)
- Qt: `QSystemTrayIcon.showMessage()` (funktioniert überall, aber basic)

**Empfehlung:** Qt-Tray-Messages als Fallback, plattformspezifische für bessere UX

### 📋 Linux-spezifische Anpassungen:

#### Template-Handler

**USB-Handler (Linux):**
```python
def _detect_linux_drives(self) -> List[dict]:
    """
    Linux: USB-Laufwerke via /sys/block/*/removable
    """
    drives = []

    # /media/USER/*
    media_path = Path("/media") / os.getlogin()
    if media_path.exists():
        drives.extend([
            (str(d), f"💾 {d.name}")
            for d in media_path.iterdir()
            if d.is_dir()
        ])

    # /mnt/* (manuell gemountet)
    mnt_path = Path("/mnt")
    if mnt_path.exists():
        drives.extend([
            (str(d), f"💾 {d.name}")
            for d in mnt_path.iterdir()
            if d.is_dir() and d.name not in ["wsl", "wslg"]
        ])

    # /run/media/USER/* (Fedora, RHEL)
    run_media = Path("/run/media") / os.getlogin()
    if run_media.exists():
        drives.extend([
            (str(d), f"💾 {d.name}")
            for d in run_media.iterdir()
            if d.is_dir()
        ])

    return drives
```

**OneDrive-Handler (Linux):**
- OneDrive hat keinen offiziellen Linux-Client
- **Alternative:** rclone mit OneDrive-Backend (funktioniert!)
- **Weitere Option:** onedriver (FUSE, inoffiziell)

**Synology-Handler (Linux):**
- SMB/CIFS funktioniert überall (via smbclient)
- Keine Änderung nötig

#### Dependencies (Linux)

**Zusätzliche Pakete:**
```bash
# Ubuntu/Debian
sudo apt install python3-keyring libsecret-1-0 smbclient cron

# Fedora/RHEL
sudo dnf install python3-keyring libsecret samba-client cronie

# Arch
sudo pacman -S python-keyring libsecret smbclient cronie
```

**requirements-linux.txt:**
```
# Linux-spezifisch
secretstorage>=3.3.0         # Keyring-Backend für Linux
python-notify2>=0.3.1        # D-Bus Notifications
pyxdg>=0.28                  # XDG Base Directory Specification
```

#### Packaging (Linux)

**Optionen:**
1. **PyPI** - `pip install scrat-backup` (einfachste)
2. **.deb** - Debian/Ubuntu-Paket (via `stdeb` oder `fpm`)
3. **.rpm** - Fedora/RHEL-Paket (via `fpm`)
4. **AppImage** - Portable (via `python-appimage`)
5. **Flatpak** - Sandboxed (via `flatpak-builder`)
6. **Snap** - Ubuntu Store (via `snapcraft`)

**Empfehlung für Start:** PyPI + .deb (am weitesten verbreitet)

### 🧪 Testing-Strategie

**Matrix:**
```yaml
os: [ubuntu-latest, windows-latest, macos-latest]
python: [3.9, 3.10, 3.11, 3.12]
```

**Pytest-Marker:**
```python
@pytest.mark.windows
def test_windows_task_scheduler():
    ...

@pytest.mark.linux
def test_linux_cron():
    ...
```

**CI/CD (GitHub Actions):**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pytest --cov
```

### 📦 Linux-Implementierungsplan

#### Phase 1: Basis-Kompatibilität (1 Woche)
- [x] Plattform-Scheduler abstrahieren (`platform_scheduler.py`)
- [x] Autostart abstrahieren (`autostart.py`)
- [ ] XDG User Directories Support
- [ ] Linux-Testing lokal (VM oder WSL2)

#### Phase 2: Template-Handler (1 Woche)
- [ ] USB-Handler: Linux-Laufwerks-Erkennung
- [ ] OneDrive-Handler: rclone-basiert (funktioniert auf beiden)
- [ ] Synology-Handler: SMB (funktioniert auf beiden)
- [ ] Template-Verfügbarkeits-Check plattformspezifisch

#### Phase 3: Packaging (1 Woche)
- [ ] PyPI-Paket (plattformunabhängig)
- [ ] .deb-Paket für Debian/Ubuntu
- [ ] Desktop-Datei (`scrat-backup.desktop`)
- [ ] Icon-Installation (`/usr/share/icons/`)

#### Phase 4: Testing & CI (1 Woche)
- [ ] GitHub Actions Matrix (Ubuntu, Windows, macOS)
- [ ] Plattformspezifische Tests
- [ ] Integration-Tests auf allen Plattformen

**Gesamt: ca. 4 Wochen für volle Linux-Unterstützung**

### 🎯 Linux-Priorität

**Empfehlung:**
1. **Jetzt:** Plattform-Abstraktion implementieren (während Template-System gebaut wird)
2. **Parallel:** Templates so designen, dass sie plattformunabhängig sind
3. **Später:** Linux-Packaging und spezifische Features

**Vorteil:** Code von Anfang an plattformunabhängig → keine Refactoring-Arbeit später

---

## Implementierungsstatus

### ✅ Phase 1: Template-System (ABGESCHLOSSEN)

**Zeitraum:** 2026-02-01
**Status:** ✅ Fertig

#### Implementierte Komponenten:

##### 1. Core-System
- ✅ **TemplateHandler** (`src/templates/handlers/base.py`)
  - Abstrakte Basis-Klasse für alle Handler
  - `check_availability()` - Plattformspezifische Verfügbarkeits-Prüfung
  - `setup()` - Template-Setup durchführen
  - `validate()` - Config validieren
  - `is_platform_supported()` - Plattform-Check

- ✅ **TemplateManager** (`src/core/template_manager.py`)
  - Lädt Templates aus System + User-Verzeichnissen
  - `get_available_templates()` - Nur verfügbare Templates
  - `get_template_by_id()` - Spezifisches Template laden
  - `create_template()` - User-Templates erstellen
  - `validate_template()` - Template-Validierung
  - Kategorisierung (local, cloud, nas, server)

- ✅ **Template** Dataclass
  - Strukturierte Repräsentation
  - JSON ↔ Python Konvertierung
  - Config-Mapping Support

##### 2. Template-Handler (Plattformunabhängig)

- ✅ **UsbHandler** (`src/templates/handlers/usb_handler.py`)
  - **Windows:** GetDriveTypeW für Removable Drives (Typ 2)
  - **Linux:** `/media/USER/*`, `/run/media/USER/*`, `/mnt/*`
  - **macOS:** `/Volumes/*`
  - Automatische Laufwerks-Erkennung
  - Schreibzugriff-Test
  - Drive-Label-Erkennung

- ✅ **OneDriveHandler** (`src/templates/handlers/onedrive_handler.py`)
  - **Alle Plattformen:** rclone-basiert
  - rclone-Installation-Check
  - OAuth-Authentifizierung (Personal + Business)
  - Automatische rclone-Installation
    - Windows: Chocolatey
    - Linux: apt/dnf/pacman oder curl-Skript
    - macOS: Homebrew
  - Verbindungstest (`rclone lsd`)
  - Account-Info abrufen

- ✅ **SynologyHandler** (`src/templates/handlers/synology_handler.py`)
  - **Windows:** Built-in SMB via `net use`
  - **Linux/macOS:** `smbclient`
  - SMB-Freigaben scannen
  - Verbindungstest
  - Share-Info abrufen

##### 3. Template-Definitionen (JSON)

- ✅ **templates/usb.json**
  - UI-Fields: drive_selector, path, verify_writable
  - Config-Mapping für local storage
  - Availability-Check: min 1 USB-Gerät

- ✅ **templates/onedrive.json**
  - UI-Fields: account_type (Personal/Business), auth_status, login_button, path
  - Config-Mapping für rclone
  - Dependency-Check: rclone installiert

- ✅ **templates/synology.json**
  - UI-Fields: host, share (mit scan), user, password, path, test_button
  - Config-Mapping für SMB
  - Dependency-Check: smbclient (Linux)

##### 4. Plattform-Abstraktionen

- ✅ **PlatformScheduler** (`src/core/platform_scheduler.py`)
  - `WindowsTaskScheduler` - schtasks.exe
  - `LinuxCronScheduler` - crontab
  - `MacOSLaunchdScheduler` - launchd (Placeholder)
  - Factory: `get_platform_scheduler()`

- ✅ **AutostartManager** (`src/core/autostart.py`)
  - Windows: Registry `HKEY_CURRENT_USER\...\Run`
  - Linux: `.desktop` in `~/.config/autostart/`
  - macOS: LaunchAgent in `~/Library/LaunchAgents/`
  - `enable_autostart()`, `disable_autostart()`, `is_autostart_enabled()`

##### 5. Wizard V2 Integration

- ✅ **wizard_v2.py** (`src/gui/wizard_v2.py`)
  - `ModePage` - Normal vs. Experten-Modus
  - `TemplateDestinationPage` - **Mit TemplateManager-Integration!**
    - Lädt echte Templates via `TemplateManager`
    - Kategorisierte Anzeige (Lokal, Cloud, NAS, Server)
    - Dynamisches Handler-Laden
    - Verfügbarkeits-Check + Warnung
  - `NewFinishPage` - Tray-Start + Backup-Option
  - `get_config()` - Config-Generierung

### ✅ Phase 2: Wizard-Umbau (ABGESCHLOSSEN)

**Zeitraum:** 2026-02-01
**Status:** ✅ 100% fertig (UI/Templates)

#### ✅ Fertig:
- ✅ Template-Auswahl-UI (kompaktes Grid, 5 Spalten)
- ✅ Alle Templates in EINEM Grid (keine Kategorien)
- ✅ Handler-Loading (dynamisch)
- ✅ Verfügbarkeits-Check + visuelle Markierung (⚠️)
- ✅ ModePage optimiert (Texte vollständig sichtbar)
- ✅ 7 Templates verfügbar (USB, OneDrive, Google Drive, Dropbox, Nextcloud, Synology, QNAP)
- ✅ Wizard V2 produktionsreif (UI-Ebene)

#### ✅ DynamicTemplateForm (NEU implementiert)
- ✅ **DynamicTemplateForm** (`src/gui/dynamic_template_form.py`)
  - Field-Type-Handler implementiert:
    - ✅ `text` - QLineEdit mit Validation & Placeholder
    - ✅ `password` - QLineEdit mit EchoMode
    - ✅ `combo` - QComboBox (editierbar)
    - ✅ `button` - QPushButton mit Action-Binding
    - ✅ `status` - Dynamisches Status-Label
  - ✅ Handler-Funktionen aufrufen:
    - `scan_shares()` - SMB-Freigaben scannen (Synology, QNAP)
    - `test_connection()` - Verbindungstest (alle Typen)
    - `oauth_login()` - OAuth-Flow (OneDrive, Google Drive, Dropbox)
  - ✅ Validierung implementiert:
    - Required-Felder prüfen
    - Regex-Validation
    - Fehler-Messages
  - ✅ Integration in wizard_v2.py abgeschlossen
  - ✅ Signal-System (`config_changed`, `action_requested`)

### ✅ Phase 3: Wizard V3 - Komplettüberarbeitung (ABGESCHLOSSEN)

**Zeitraum:** 2026-02-01
**Status:** ✅ 95% fertig - **PRODUKTIONSREIF!**

#### ✅ Dark Mode System
- ✅ **ThemeManager** (`src/gui/theme_manager.py`)
  - Automatische System-Dark-Mode-Erkennung
  - Windows 11 Light Theme (aus bestehendem theme.py)
  - Windows 11 Dark Theme (neu erstellt)
  - Manueller Toggle (Light ↔ Dark)
  - QSettings-Speicherung der Präferenz
  - Signal bei Theme-Änderung
  - Integration in main.py ✅

#### ✅ Neue Wizard-Pages (Barrierefreiheit & UX)
- ✅ **StartPage** (`src/gui/wizard_pages.py`)
  - Radio-Buttons statt Karten (Barrierefreiheit ✓)
  - Config-Check (Ersteinrichtung vs. Bestehendes System)
  - Unterschiedliche Optionen je nach Zustand:
    - **Ersteinrichtung:** Backup einrichten / Restore
    - **Bestehendes System:** Einstellungen ändern / Ziel hinzufügen / Restore / Experten-Modus
  - Klickbare Frames mit Hover-Effekten
  - Dynamisches Routing (nextId())

- ✅ **SourceSelectionPage** (`src/gui/wizard_pages.py`)
  - Automatische Bibliotheken-Erkennung (plattformabhängig):
    - Windows: Documents, Pictures, Videos, Music, Desktop, Downloads
    - Linux: Gleiche mit XDG-Pfaden
    - macOS: Angepasste Pfade (Movies statt Videos)
  - Checkbox-Liste für Standard-Bibliotheken
  - "Ordner hinzufügen"-Button mit QFileDialog
  - Liste der eigenen Ordner mit Entfernen-Funktion
  - **Plattformspezifische Ausschlüsse:**
    - Plattformunabhängig: `*.tmp`, `*.cache`, `.git/`, `node_modules/`, etc.
    - Windows: `Thumbs.db`, `desktop.ini`, `~$*`, `$RECYCLE.BIN/`
    - Linux: `.Trash-*/`, `.thumbnails/`, `*.~lock.*`, `.directory`
    - macOS: `.DS_Store`, `.AppleDouble/`, `.Spotlight-V100/`
  - Validierung (mindestens eine Quelle erforderlich)

- ✅ **FinishPage** (erweitert)
  - Detaillierte Zusammenfassung:
    - Gewählte Aktion (Backup/Restore/Edit)
    - Quellen-Liste (erste 5 + Anzahl)
    - Ausschlüsse (Anzahl)
    - Backup-Ziel (mit Icon)
  - Optionen: Backup jetzt starten / Tray starten
  - Hinweis bei Restore (noch nicht implementiert)

#### ✅ Integration & Config
- ✅ **wizard_v2.py** komplett überarbeitet
  - Neue Page-Reihenfolge: Start → Source → Destination → Finish
  - Page-IDs definiert (PAGE_START, PAGE_SOURCE, etc.)
  - Dynamisches Routing basierend auf Auswahl
  - get_config() angepasst für neues Format

- ✅ **main.py** Integration
  - Import auf `SetupWizardV2` geändert
  - `save_wizard_config()` angepasst:
    - Nutzt neue Config-Struktur
    - Speichert plattformspezifische Ausschlüsse
    - Template-basierte Destinations
    - Lesbare Template-Namen

#### ✅ DynamicTemplateForm (bereits implementiert)
- ✅ Field-Type-Handler (text, password, combo, button, status)
- ✅ Handler-Aktionen (scan_shares, test_connection, oauth_login)
- ✅ Validierung (required, regex)

#### 🚧 Noch offen:
- [ ] Tray-Icon mit Theme-Toggle
- [ ] Restore-Flow (eigener Wizard)
- [ ] Template-Manager-Tab für MainWindow
- [ ] Schedule-Page (Zeitplan)
- [ ] Encryption-Page (Verschlüsselung)

### 📋 Phase 4: Polish (TEILWEISE FERTIG)

**Geplant:** 2026-02-09 - 2026-02-15

- [x] **Weitere Templates** ✅
  - [x] Google Drive (rclone)
  - [x] Nextcloud (WebDAV)
  - [x] QNAP NAS (SMB)
  - [x] Dropbox (rclone)
- [ ] Noch mehr Templates (iCloud, AWS S3, FTP, ownCloud, pCloud)
- [ ] Icons für Templates (aktuell: Emojis)
- [ ] Lokalisierung (DE/EN)
- [ ] Tests für Handler
- [ ] Dokumentation erweitern

---

## Test-Anleitung

### Voraussetzungen

```bash
# Python 3.9+ mit venv
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# oder
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -e .
```

### 1. Template-System testen

#### TemplateManager

```python
from src.core.template_manager import TemplateManager

# Manager initialisieren
manager = TemplateManager()

# Alle Templates laden
all_templates = manager.get_all_templates()
print(f"Alle Templates: {len(all_templates)}")

# Nur verfügbare Templates
available = manager.get_available_templates()
print(f"Verfügbare: {len(available)}")

for template in available:
    print(f"  - {template.id}: {template.display_name} ({template.category})")

# Spezifisches Template
usb = manager.get_template_by_id("usb")
print(f"\nUSB-Template: {usb.display_name}")
print(f"  Plattformen: {usb.platforms}")
print(f"  UI-Felder: {len(usb.ui_fields)}")
```

#### USB-Handler testen

```python
from src.templates.handlers.usb_handler import UsbHandler

# Template laden
usb_template = manager.get_template_by_id("usb")
handler = UsbHandler(usb_template.raw_data)

# Verfügbarkeit prüfen
is_available, error = handler.check_availability()
print(f"\nUSB verfügbar: {is_available}")
if error:
    print(f"  Fehler: {error}")

# Laufwerke erkennen
drives = handler.detect_usb_drives()
print(f"\nGefundene USB-Laufwerke: {len(drives)}")
for drive in drives:
    print(f"  - {drive['path']}: {drive['label']} ({drive.get('size', 'N/A')})")

# Setup durchführen (Beispiel)
if drives:
    config = {
        "drive": drives[0]["path"],
        "path": "Backups",
        "verify_writable": True
    }

    success, result_config, error = handler.setup(config)
    print(f"\nSetup erfolgreich: {success}")
    if success:
        print(f"  Config: {result_config}")
    else:
        print(f"  Fehler: {error}")
```

#### OneDrive-Handler testen

```python
from src.templates.handlers.onedrive_handler import OneDriveHandler

onedrive_template = manager.get_template_by_id("onedrive")
handler = OneDriveHandler(onedrive_template.raw_data)

# rclone-Check
is_available, error = handler.check_availability()
print(f"\nOneDrive verfügbar: {is_available}")
if error:
    print(f"  {error}")

# Authentifizierungs-Status (wenn rclone installiert)
if is_available:
    is_auth, status = handler.check_authentication()
    print(f"  Status: {status}")
```

#### Synology-Handler testen

```python
from src.templates.handlers.synology_handler import SynologyHandler

synology_template = manager.get_template_by_id("synology")
handler = SynologyHandler(synology_template.raw_data)

# Verfügbarkeit
is_available, error = handler.check_availability()
print(f"\nSynology verfügbar: {is_available}")

# Freigaben scannen (Beispiel - erfordert Synology im Netzwerk)
if is_available:
    success, shares, error = handler.scan_shares(
        "192.168.1.100",  # Synology IP
        "admin",
        "password"
    )

    if success:
        print(f"  Freigaben: {shares}")
    else:
        print(f"  Fehler: {error}")
```

### 2. Wizard V2 testen

```bash
# Wizard starten
python src/gui/wizard_v2.py
```

**Erwartetes Verhalten:**

1. **ModePage**
   - Zeigt zwei Karten: "Einfacher Modus" (empfohlen) und "Experten-Modus"
   - "Weiter" führt zu TemplateDestinationPage

2. **TemplateDestinationPage**
   - Lädt Templates automatisch
   - Zeigt Kategorien: 📁 Lokal, ☁️ Cloud, 🖥️ NAS
   - Templates werden als Buttons angezeigt
   - Klick auf Template → Handler wird geladen
   - Verfügbarkeits-Check wird angezeigt
   - **Aktuell:** Placeholder-Formular (🚧 wird implementiert)

3. **NewFinishPage**
   - Zeigt Zusammenfassung
   - Checkboxen: "Backup jetzt starten" + "Tray starten"
   - "Fertig" → get_config() gibt Wizard-Config zurück

### 3. Plattformspezifische Tests

#### Linux-USB-Erkennung testen

```python
# Auf Linux-System
from src.templates.handlers.usb_handler import UsbHandler

handler = UsbHandler({})
drives = handler._detect_linux_drives()

# Sollte USB-Laufwerke in /media, /run/media, /mnt finden
print(f"Linux USB-Laufwerke: {drives}")
```

#### Windows-USB-Erkennung testen

```python
# Auf Windows-System
from src.templates.handlers.usb_handler import UsbHandler

handler = UsbHandler({})
drives = handler._detect_windows_drives()

# Sollte USB-Laufwerke (Typ 2) finden: D:\, E:\, etc.
print(f"Windows USB-Laufwerke: {drives}")
```

#### Scheduler testen

```python
from src.core.platform_scheduler import get_platform_scheduler

scheduler = get_platform_scheduler()
if scheduler:
    print(f"Scheduler: {scheduler.__class__.__name__}")

    # Task registrieren (Beispiel)
    success = scheduler.register_task(
        "test-backup",
        "startup",
        "python",
        ["-m", "scrat_backup", "--backup"]
    )
    print(f"Task registriert: {success}")

    # Task entfernen
    scheduler.unregister_task("test-backup")
```

#### Autostart testen

```python
from src.core.autostart import AutostartManager

manager = AutostartManager()

# Prüfen
is_enabled = manager.is_autostart_enabled()
print(f"Autostart aktiviert: {is_enabled}")

# Aktivieren (Beispiel)
# success = manager.enable_autostart()
# print(f"Autostart aktiviert: {success}")
```

### 4. Template erstellen testen

```python
from src.core.template_manager import TemplateManager

manager = TemplateManager()

# Neues Template erstellen
custom_template = {
    "id": "my_custom_server",
    "version": "1.0",
    "display_name": "Mein Server",
    "icon": "🖥️",
    "description": "Backup auf meinen Server",
    "category": "server",
    "storage_type": "sftp",
    "handler": "sftp_handler",
    "platforms": ["windows", "linux"],
    "ui_fields": [
        {
            "name": "host",
            "type": "text",
            "label": "Server-Adresse",
            "required": True
        }
    ],
    "config_mapping": {
        "type": "sftp",
        "host": "${host}",
        "port": 22
    }
}

# Speichern
template = manager.create_template(custom_template, user_template=True)
print(f"Template erstellt: {template.id}")

# Prüfen
custom = manager.get_template_by_id("my_custom_server")
print(f"Geladen: {custom.display_name}")

# Löschen
# manager.delete_template("my_custom_server")
```

### 5. Fehlerbehandlung testen

#### Template mit fehlendem Handler

```python
broken_template = {
    "id": "broken",
    "display_name": "Broken Template",
    "storage_type": "unknown",
    "handler": "nonexistent_handler",  # Existiert nicht
    "platforms": ["windows"]
}

manager.create_template(broken_template)

# Sollte Warnung loggen, aber nicht abstürzen
templates = manager.get_available_templates()
```

#### Nicht verfügbares Template

```python
# OneDrive ohne rclone
from src.templates.handlers.onedrive_handler import OneDriveHandler
import shutil

# rclone entfernen (simuliert)
# shutil.which("rclone") → None

handler = OneDriveHandler({})
is_available, error = handler.check_availability()
# Sollte (False, "rclone ist nicht installiert...") zurückgeben
```

### 6. Integration testen

```python
# Kompletter Flow: Template → Handler → Config
from src.core.template_manager import TemplateManager

manager = TemplateManager()

# 1. Template laden
template = manager.get_template_by_id("usb")

# 2. Handler erstellen
from src.templates.handlers.usb_handler import UsbHandler
handler = UsbHandler(template.raw_data)

# 3. Setup durchführen
drives = handler.detect_usb_drives()
if drives:
    config_input = {
        "drive": drives[0]["path"],
        "path": "Backups"
    }

    success, final_config, error = handler.setup(config_input)

    # 4. Config sollte bereit sein für ConfigManager
    print(f"Finale Config: {final_config}")
    # {'type': 'local', 'path': 'D:\\Backups', 'name': 'USB-Backup (D:)', ...}
```

### Troubleshooting

#### "ModuleNotFoundError: No module named 'PySide6'"

```bash
pip install PySide6
```

#### "No templates found"

```bash
# Templates-Verzeichnis prüfen
ls templates/
# Sollte zeigen: usb.json, onedrive.json, synology.json

# Oder absoluten Pfad prüfen
python -c "from src.core.template_manager import TemplateManager; m = TemplateManager(); print(m.system_templates_dir)"
```

#### "Handler not found"

```bash
# Handler-Verzeichnis prüfen
ls src/templates/handlers/
# Sollte zeigen: base.py, usb_handler.py, onedrive_handler.py, synology_handler.py

# Python-Path prüfen
python -c "import sys; sys.path.insert(0, 'src'); from templates.handlers.usb_handler import UsbHandler; print('OK')"
```

---

## Änderungshistorie

| Datum      | Änderung                                    |
|------------|---------------------------------------------|
| 2026-02-01 | Initial erstellt - Gesamtkonzept & Roadmap |
| 2026-02-01 | Linux-Kompatibilitätsplan hinzugefügt       |
|            | - platform_scheduler.py erstellt           |
|            | - autostart.py erstellt                    |
| 2026-02-01 | **Phase 1 abgeschlossen: Template-System** |
|            | - TemplateManager implementiert            |
|            | - TemplateHandler (Base) erstellt          |
|            | - UsbHandler (plattformunabhängig)         |
|            | - OneDriveHandler (rclone-basiert)         |
|            | - SynologyHandler (SMB)                    |
|            | - 3 Template-JSONs (USB, OneDrive, Synology)|
|            | - wizard_v2.py mit TemplateManager         |
|            | - Test-Anleitung hinzugefügt               |
| 2026-02-01 | **Wizard V2 UI optimiert**                 |
|            | - ModePage: Cards-Größe optimiert          |
|            | - TemplateDestinationPage: Kompaktes Grid  |
|            | - Alle Templates in 1 Grid (5 Spalten)     |
|            | - Verfügbarkeits-Check mit visueller Markierung |
| 2026-02-01 | **4 neue Templates hinzugefügt**           |
|            | - GoogleDriveHandler (rclone)              |
|            | - NextcloudHandler (WebDAV)                |
|            | - QnapHandler (SMB)                        |
|            | - DropboxHandler (rclone)                  |
|            | - **Gesamt: 7 Templates verfügbar**       |
| 2026-02-01 | **DynamicTemplateForm implementiert**     |
|            | - Dynamische Form-Generierung aus ui_fields|
|            | - 5 Feldtypen unterstützt (text, password, combo, button, status) |
|            | - Handler-Actions integriert (scan_shares, test_connection, oauth_login) |
|            | - Validierung (required, regex)           |
|            | - Integration in wizard_v2.py             |
|            | - Signal-System für config_changed        |
|            | - **Wizard jetzt vollständig funktionsfähig** |
| 2026-02-01 | **🎉 Wizard V3 - Komplettüberarbeitung**  |
|            | **Dark Mode System:**                      |
|            | - ThemeManager mit Auto-Detection          |
|            | - Windows 11 Light & Dark Themes           |
|            | - Toggle-Funktion & QSettings-Speicherung  |
|            | **Neue Wizard-Pages (Barrierefreiheit):**  |
|            | - StartPage: Radio-Buttons, Config-Check   |
|            | - SourceSelectionPage: Bibliotheken + Eigene Ordner |
|            | - Plattformspezifische Ausschlüsse (Win/Linux/macOS) |
|            | - FinishPage: Erweiterte Zusammenfassung   |
|            | **Integration:**                           |
|            | - wizard_v2.py: Neue Page-Reihenfolge      |
|            | - main.py: SetupWizardV2 integriert        |
|            | - save_wizard_config(): Neues Format       |
|            | **Flow:** Start → Source → Destination → Finish |
|            | - **WIZARD V3 PRODUKTIONSREIF! 🚀**        |
| 2026-02-02 | **♿ Barrierefreiheit & UX-Verbesserungen** |
|            | **Visuelles Design:**                      |
|            | - StartPage & ModePage: Einheitlicher Style |
|            | - Keine Frames/Borders mehr, nur Radio-Buttons |
|            | - Font-Größen harmonisiert (16px/13px)    |
|            | - Besserer Kontrast (Hover: #e8e8e8, Selection: #d0d0d0) |
|            | **Ordner-Auswahl (SourceSelectionPage):**  |
|            | - Icons (📁) vor allen Ordnern             |
|            | - Farbliche Hervorhebung (blau + fett)    |
|            | - Hover-Effekt auf Ordner-Einträgen        |
|            | - Selection mit grauer Unterlegung         |
|            | **🎹 Tastatur-Bedienung (Barrierefreiheit):**|
|            | - Textfeld für direkte Pfad-Eingabe       |
|            | - Schnellauswahl-Buttons (Home, Desktop, Dokumente) |
|            | - Vollständige Tab-Navigation              |
|            | - "Durchsuchen"-Button für Maus-Nutzer    |
|            | **Lokalisierung:**                         |
|            | - Qt-Übersetzungen geladen (deutsche Dialoge) |
|            | - QTranslator in run_wizard.py & main.py   |
|            | **Einschränkungen:**                       |
|            | - QFileDialog selbst nicht vollständig tastatur-bedienbar (Qt-Limitation) |
|            | - Workaround: Textfeld + Schnellauswahl (vollständig barrierefrei) |
