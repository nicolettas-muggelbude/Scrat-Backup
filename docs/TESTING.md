# Scrat-Backup – Test-Anleitung

## Voraussetzungen

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS  |  venv\Scripts\activate  # Windows
pip install -e .
```

---

## 1. Template-System testen

### TemplateManager

```python
from src.core.template_manager import TemplateManager

manager = TemplateManager()

all_templates = manager.get_all_templates()
print(f"Alle Templates: {len(all_templates)}")

available = manager.get_available_templates()
print(f"Verfügbare: {len(available)}")
for template in available:
    print(f"  - {template.id}: {template.display_name} ({template.category})")

usb = manager.get_template_by_id("usb")
print(f"\nUSB-Template: {usb.display_name}")
print(f"  Plattformen: {usb.platforms}")
print(f"  UI-Felder: {len(usb.ui_fields)}")
```

### USB-Handler

```python
from src.templates.handlers.usb_handler import UsbHandler

usb_template = manager.get_template_by_id("usb")
handler = UsbHandler(usb_template.raw_data)

is_available, error = handler.check_availability()
print(f"USB verfügbar: {is_available}")
if error:
    print(f"  Fehler: {error}")

drives = handler.detect_usb_drives()
print(f"Gefundene USB-Laufwerke: {len(drives)}")
for drive in drives:
    print(f"  - {drive['path']}: {drive['label']} ({drive.get('size', 'N/A')})")

if drives:
    config = {"drive": drives[0]["path"], "path": "Backups", "verify_writable": True}
    success, result_config, error = handler.setup(config)
    print(f"Setup erfolgreich: {success}")
    print(f"  Config: {result_config}" if success else f"  Fehler: {error}")
```

### OneDrive-Handler

```python
from src.templates.handlers.onedrive_handler import OneDriveHandler

onedrive_template = manager.get_template_by_id("onedrive")
handler = OneDriveHandler(onedrive_template.raw_data)

is_available, error = handler.check_availability()
print(f"OneDrive verfügbar: {is_available}")
if error:
    print(f"  {error}")

if is_available:
    is_auth, status = handler.check_authentication()
    print(f"  Status: {status}")
```

### Synology-Handler

```python
from src.templates.handlers.synology_handler import SynologyHandler

synology_template = manager.get_template_by_id("synology")
handler = SynologyHandler(synology_template.raw_data)

is_available, error = handler.check_availability()
print(f"Synology verfügbar: {is_available}")

if is_available:
    success, shares, error = handler.scan_shares("192.168.1.100", "admin", "password")
    print(f"  Freigaben: {shares}" if success else f"  Fehler: {error}")
```

---

## 2. Wizard testen

```bash
python src/gui/wizard_v2.py
```

**Erwarteter Flow:**
1. **StartPage** – Ersteinrichtung vs. Bestehendes System, Radio-Buttons
2. **SourceSelectionPage** – Bibliotheken auswählen, eigene Ordner hinzufügen
3. **TemplateDestinationPage** – Template-Grid, Handler laden, DynamicTemplateForm
4. **FinishPage** – Zusammenfassung, "Backup jetzt starten" / "Tray starten"

---

## 3. Plattformspezifische Tests

### Linux-USB-Erkennung

```python
from src.templates.handlers.usb_handler import UsbHandler
handler = UsbHandler({})
drives = handler._detect_linux_drives()
print(f"Linux USB-Laufwerke: {drives}")  # /media, /run/media, /mnt
```

### Windows-USB-Erkennung

```python
from src.templates.handlers.usb_handler import UsbHandler
handler = UsbHandler({})
drives = handler._detect_windows_drives()
print(f"Windows USB-Laufwerke: {drives}")  # Typ 2 (Removable)
```

### Scheduler

```python
from src.core.platform_scheduler import get_platform_scheduler

scheduler = get_platform_scheduler()
if scheduler:
    print(f"Scheduler: {scheduler.__class__.__name__}")
    success = scheduler.register_task("test-backup", "startup", "python", ["-m", "scrat_backup", "--backup"])
    print(f"Task registriert: {success}")
    scheduler.unregister_task("test-backup")
```

### Autostart

```python
from src.core.autostart import AutostartManager
manager = AutostartManager()
print(f"Autostart aktiviert: {manager.is_autostart_enabled()}")
# manager.enable_autostart()
```

---

## 4. Template erstellen testen

```python
from src.core.template_manager import TemplateManager

manager = TemplateManager()

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
        {"name": "host", "type": "text", "label": "Server-Adresse", "required": True}
    ],
    "config_mapping": {"type": "sftp", "host": "${host}", "port": 22}
}

template = manager.create_template(custom_template, user_template=True)
print(f"Template erstellt: {template.id}")

custom = manager.get_template_by_id("my_custom_server")
print(f"Geladen: {custom.display_name}")
# manager.delete_template("my_custom_server")
```

---

## 5. Fehlerbehandlung testen

### Template mit fehlendem Handler

```python
broken_template = {
    "id": "broken",
    "display_name": "Broken Template",
    "storage_type": "unknown",
    "handler": "nonexistent_handler",
    "platforms": ["windows"]
}
manager.create_template(broken_template)
templates = manager.get_available_templates()  # Sollte nicht abstürzen
```

### Nicht verfügbares Template

```python
from src.templates.handlers.onedrive_handler import OneDriveHandler
handler = OneDriveHandler({})
is_available, error = handler.check_availability()
# Ohne rclone: (False, "rclone ist nicht installiert...")
```

---

## 6. Integration testen (kompletter Flow)

```python
from src.core.template_manager import TemplateManager
from src.templates.handlers.usb_handler import UsbHandler

manager = TemplateManager()
template = manager.get_template_by_id("usb")
handler = UsbHandler(template.raw_data)

drives = handler.detect_usb_drives()
if drives:
    config_input = {"drive": drives[0]["path"], "path": "Backups"}
    success, final_config, error = handler.setup(config_input)
    print(f"Finale Config: {final_config}")
    # {'type': 'local', 'path': 'D:\\Backups', 'name': 'USB-Backup (D:)', ...}
```

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'PySide6'"**
```bash
pip install PySide6
```

**"No templates found"**
```bash
ls templates/                 # usb.json, onedrive.json, synology.json vorhanden?
python -c "from src.core.template_manager import TemplateManager; m = TemplateManager(); print(m.system_templates_dir)"
```

**"Handler not found"**
```bash
ls src/templates/handlers/    # base.py, usb_handler.py, onedrive_handler.py, synology_handler.py
python -c "import sys; sys.path.insert(0, 'src'); from templates.handlers.usb_handler import UsbHandler; print('OK')"
```
