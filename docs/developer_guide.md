# Scrat-Backup - Developer Guide

Willkommen zum Developer Guide für Scrat-Backup! Dieser Guide hilft dir, die Codebase zu verstehen und effektiv beizutragen.

## 📋 Inhaltsverzeichnis

- [Projekt-Übersicht](#projekt-übersicht)
- [Architektur](#architektur)
- [Entwicklungsumgebung](#entwicklungsumgebung)
- [Code-Organisation](#code-organisation)
- [Core-Module](#core-module)
- [GUI-Entwicklung](#gui-entwicklung)
- [Storage-Backends](#storage-backends)
- [Testing](#testing)
- [Debugging](#debugging)
- [Best Practices](#best-practices)

---

## Projekt-Übersicht

### Ziel

Scrat-Backup ist ein benutzerfreundliches Backup-Tool für Windows-Privatnutzer mit:
- Verschlüsselten Backups (AES-256-GCM, Pflicht)
- Inkrementellen Backups mit Versionierung
- Flexiblen Storage-Backends (USB, SFTP, WebDAV, Rclone)
- Einfacher GUI im Windows 11-Stil

### Technologie-Stack

- **Python 3.10+**: Hauptsprache
- **PyQt6**: GUI-Framework
- **SQLite**: Metadaten-Speicherung
- **cryptography**: AES-256-GCM Verschlüsselung
- **py7zr**: 7z-Komprimierung
- **pytest**: Testing-Framework

### Architektur-Prinzipien

1. **Schichtenarchitektur**: GUI → Controller → Business Logic → Storage
2. **Lose Kopplung**: Event-Bus für Kommunikation
3. **Testbarkeit**: Jede Schicht isoliert testbar
4. **Erweiterbarkeit**: Plugin-System für Storage-Backends

---

## Architektur

### Überblick

```
┌─────────────────────────────────────────────┐
│           GUI Layer (PyQt6)                 │
│  - main_window.py                           │
│  - backup_tab.py                            │
│  - restore_tab.py                           │
│  - settings_window.py                       │
└──────────────────┬──────────────────────────┘
                   │ QThread Signals
┌──────────────────▼──────────────────────────┐
│         Core Business Logic                 │
│  - backup_engine.py                         │
│  - restore_engine.py                        │
│  - scanner.py                               │
│  - encryptor.py                             │
│  - compressor.py                            │
└──────────────────┬──────────────────────────┘
                   │ StorageBackend Interface
┌──────────────────▼──────────────────────────┐
│      Storage Abstraction Layer              │
│  - base.py (ABC)                            │
│  - usb_storage.py                           │
│  - sftp_storage.py                          │
│  - webdav_storage.py                        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│        Data & Configuration                 │
│  - SQLite (metadata.db)                     │
│  - JSON (config.json)                       │
└─────────────────────────────────────────────┘
```

### Datenfluss: Backup

```
1. User klickt "Backup starten" (GUI)
   ↓
2. BackupWorker (QThread) gestartet
   ↓
3. Scanner scannt Quell-Ordner
   ↓
4. Für jede Datei:
   - Lesen (8MB Chunks)
   - Komprimieren (7z)
   - Verschlüsseln (AES-256-GCM)
   - Zu Storage hochladen
   ↓
5. Metadaten in SQLite speichern
   ↓
6. Signal an GUI: Backup abgeschlossen
```

### Datenfluss: Restore

```
1. User wählt Zeitpunkt und Dateien
   ↓
2. Metadaten-Abfrage in SQLite
   ↓
3. Für jede Datei:
   - Von Storage herunterladen
   - Entschlüsseln (AES-256-GCM)
   - Dekomprimieren (7z)
   - Schreiben zu Ziel
   ↓
4. Signal an GUI: Restore abgeschlossen
```

---

## Entwicklungsumgebung

### Setup

```bash
# Repository klonen
git clone https://github.com/your-username/scrat-backup.git
cd scrat-backup

# Virtual Environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Verifizieren
./dev.sh check
```

### Entwicklungs-Tools

**dev.sh Script:**
```bash
./dev.sh format    # Code formatieren
./dev.sh check     # Quality-Checks
./dev.sh test      # Tests
./dev.sh run       # Programm starten
```

**Manuelle Nutzung:**
```bash
# Code formatieren
black src/ tests/
isort src/ tests/

# Linting
flake8 src/ tests/

# Type-Checking
mypy src/

# Tests
pytest tests/ -v
pytest tests/ --cov=src  # Mit Coverage
```

### IDE-Setup

**VS Code:**

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true
}
```

**PyCharm:**
- Project Interpreter: `./venv/`
- Code Style: Black
- Enable pytest

---

## Code-Organisation

### Verzeichnis-Struktur

```
src/
├── __init__.py
├── main.py                 # Entry Point
│
├── gui/                    # GUI-Komponenten
│   ├── __init__.py
│   ├── main_window.py      # Hauptfenster
│   ├── backup_tab.py       # Backup-Tab
│   ├── restore_tab.py      # Restore-Tab
│   ├── history_tab.py      # Verlauf-Tab
│   ├── settings_window.py  # Einstellungen
│   ├── wizard.py           # Setup-Wizard
│   └── notification.py     # Benachrichtigungen
│
├── core/                   # Business Logic
│   ├── __init__.py
│   ├── backup_engine.py    # Backup-Orchestrierung
│   ├── restore_engine.py   # Restore-Orchestrierung
│   ├── scanner.py          # Datei-Scanner
│   ├── compressor.py       # 7z-Komprimierung
│   ├── encryptor.py        # AES-256-GCM
│   ├── scheduler.py        # Zeitplanung
│   ├── metadata_manager.py # SQLite-Operationen
│   └── logger.py           # Logging
│
├── storage/                # Storage-Backends
│   ├── __init__.py
│   ├── base.py             # StorageBackend ABC
│   ├── usb_storage.py      # USB/Lokale Laufwerke
│   ├── sftp_storage.py     # SFTP
│   ├── webdav_storage.py   # WebDAV
│   └── rclone_storage.py   # Rclone-Wrapper
│
├── utils/                  # Hilfsfunktionen
│   ├── __init__.py
│   ├── config.py           # Konfigurations-Management
│   ├── event_bus.py        # Event-System
│   ├── windows_helper.py   # Windows-APIs
│   └── path_resolver.py    # Pfad-Auflösung
│
└── models/                 # Datenmodelle
    ├── __init__.py
    ├── backup_job.py       # BackupJob Dataclass
    ├── restore_job.py      # RestoreJob Dataclass
    └── config_models.py    # Config Dataclasses
```

### Namenskonventionen

**Dateien:**
- `lowercase_with_underscores.py`
- Module-Namen beschreiben Inhalt

**Klassen:**
- `PascalCase`
- `BackupEngine`, `SFTPStorage`

**Funktionen/Methoden:**
- `lowercase_with_underscores()`
- `create_backup()`, `scan_directory()`

**Konstanten:**
- `UPPER_CASE_WITH_UNDERSCORES`
- `DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024`

**Private:**
- `_leading_underscore` für interne Nutzung
- `__double_leading` für Name-Mangling (selten)

---

## Core-Module

### metadata_manager.py

**Verantwortung:** SQLite-Datenbank-Operationen

**Wichtige Klassen:**
```python
class MetadataManager:
    def __init__(self, db_path: Path):
        """Initialisiert Datenbank-Verbindung"""

    def create_backup_record(self, backup: BackupJob) -> int:
        """Erstellt neuen Backup-Eintrag"""

    def add_file_to_backup(self, backup_id: int, file_info: FileInfo) -> None:
        """Fügt Datei zu Backup hinzu"""

    def get_backups(self, destination_id: int) -> List[Backup]:
        """Holt alle Backups für Ziel"""

    def search_files(self, pattern: str) -> List[FileEntry]:
        """Sucht Dateien über alle Backups"""
```

**Beispiel:**
```python
manager = MetadataManager(Path("metadata.db"))
backup_id = manager.create_backup_record(backup_job)

for file in scanned_files:
    manager.add_file_to_backup(backup_id, file)

manager.mark_backup_complete(backup_id)
```

### encryptor.py

**Verantwortung:** AES-256-GCM Verschlüsselung

**Wichtige Klassen:**
```python
class Encryptor:
    def __init__(self, password: str):
        """Leitet Master-Key von Passwort ab"""

    def encrypt_stream(
        self,
        input_stream: BinaryIO,
        output_stream: BinaryIO,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> EncryptionResult:
        """Verschlüsselt Stream mit AES-256-GCM"""

    def decrypt_stream(
        self,
        input_stream: BinaryIO,
        output_stream: BinaryIO
    ) -> None:
        """Entschlüsselt Stream"""
```

**Wichtig:**
- Immer neue IV für jede Verschlüsselung
- Auth-Tag speichern für Integrität
- Streaming für große Dateien

### backup_engine.py

**Verantwortung:** Backup-Orchestrierung

**Wichtige Klassen:**
```python
class BackupEngine:
    def __init__(
        self,
        scanner: Scanner,
        compressor: Compressor,
        encryptor: Encryptor,
        storage: StorageBackend,
        metadata: MetadataManager
    ):
        """Dependency Injection für Testbarkeit"""

    def create_full_backup(
        self,
        sources: List[Path],
        progress_callback: Callable[[BackupProgress], None]
    ) -> BackupResult:
        """Erstellt Vollbackup"""

    def create_incremental_backup(
        self,
        sources: List[Path],
        base_backup_id: int,
        progress_callback: Callable[[BackupProgress], None]
    ) -> BackupResult:
        """Erstellt inkrementelles Backup"""
```

**Pipeline:**
```python
# 1. Scannen
files = scanner.scan(sources)

# 2. Change Detection (bei incremental)
changed_files = scanner.detect_changes(files, base_backup_id)

# 3. Für jede Datei
for file in changed_files:
    # 3a. Komprimieren
    compressed = compressor.compress_file(file)

    # 3b. Verschlüsseln
    encrypted = encryptor.encrypt_stream(compressed)

    # 3c. Hochladen
    storage.upload_file(encrypted, remote_path)

    # 3d. Metadaten speichern
    metadata.add_file_to_backup(backup_id, file)

    # 3e. Progress-Update
    progress_callback(BackupProgress(...))
```

---

## GUI-Entwicklung

### PyQt6 Basics

**Fenster erstellen:**
```python
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scrat-Backup")
        self.setGeometry(100, 100, 1024, 768)

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)

        # Layout
        layout = QVBoxLayout()
        central.setLayout(layout)
```

### Threading mit QThread

**Wichtig:** GUI darf nicht blockiert werden!

```python
from PyQt6.QtCore import QThread, pyqtSignal

class BackupWorker(QThread):
    # Signals
    progress_updated = pyqtSignal(int, str)  # percentage, filename
    backup_finished = pyqtSignal(dict)       # result
    backup_failed = pyqtSignal(Exception)

    def __init__(self, backup_engine, sources):
        super().__init__()
        self.engine = backup_engine
        self.sources = sources

    def run(self):
        """Läuft in separatem Thread"""
        try:
            def progress_callback(progress):
                self.progress_updated.emit(
                    progress.percentage,
                    progress.current_file
                )

            result = self.engine.create_full_backup(
                self.sources,
                progress_callback
            )
            self.backup_finished.emit(result)

        except Exception as e:
            self.backup_failed.emit(e)


# In Main Window
class BackupTab(QWidget):
    def start_backup(self):
        self.worker = BackupWorker(engine, sources)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.backup_finished.connect(self.on_success)
        self.worker.backup_failed.connect(self.on_error)
        self.worker.start()

    def update_progress(self, percentage, filename):
        self.progress_bar.setValue(percentage)
        self.label.setText(filename)
```

### Event-Bus Pattern

**Vorteile:** Lose Kopplung zwischen Komponenten

```python
# utils/event_bus.py
from PyQt6.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    # Singleton
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # Signals
    backup_started = pyqtSignal(str)              # backup_id
    backup_progress = pyqtSignal(str, int, str)   # id, %, file
    backup_completed = pyqtSignal(str, dict)      # id, stats


# Nutzung
event_bus = EventBus()

# Emitter (z.B. BackupWorker)
event_bus.backup_started.emit(backup_id)
event_bus.backup_progress.emit(backup_id, 50, "file.txt")

# Receiver (z.B. MainWindow)
event_bus.backup_progress.connect(self.update_ui)
```

---

## Storage-Backends

### Interface

Alle Storage-Backends implementieren `StorageBackend`:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Callable

class StorageBackend(ABC):
    @abstractmethod
    def connect(self, config: dict) -> bool:
        """Verbindung herstellen"""

    @abstractmethod
    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bool:
        """Datei hochladen"""

    @abstractmethod
    def download_file(
        self,
        remote_path: str,
        local_path: Path,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bool:
        """Datei herunterladen"""

    @abstractmethod
    def list_files(self, remote_path: str) -> List[str]:
        """Dateien auflisten"""

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Datei löschen"""

    @abstractmethod
    def get_available_space(self) -> int:
        """Freier Speicher in Bytes"""
```

### Beispiel-Implementierung

```python
# storage/usb_storage.py
from pathlib import Path
import shutil

class USBStorage(StorageBackend):
    def __init__(self):
        self.base_path: Optional[Path] = None

    def connect(self, config: dict) -> bool:
        self.base_path = Path(config["path"])
        return self.base_path.exists()

    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        progress_callback=None
    ) -> bool:
        dest = self.base_path / remote_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Mit Progress (8MB Chunks)
        with open(local_path, 'rb') as src:
            with open(dest, 'wb') as dst:
                while True:
                    chunk = src.read(8 * 1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
                    if progress_callback:
                        progress_callback(src.tell())

        return dest.exists()

    # ... weitere Methoden
```

### Storage-Backend hinzufügen

1. **Neue Datei:** `src/storage/my_storage.py`
2. **Klasse erstellen:** `class MyStorage(StorageBackend)`
3. **Interface implementieren:** Alle abstrakten Methoden
4. **Tests schreiben:** `tests/test_storage/test_my_storage.py`
5. **Registrieren:** In `src/storage/__init__.py`

---

## Testing

### Test-Struktur

```
tests/
├── conftest.py              # Pytest Fixtures
├── unit/                    # Unit-Tests
│   ├── test_encryptor.py
│   ├── test_compressor.py
│   └── test_scanner.py
├── integration/             # Integration-Tests
│   └── test_full_backup.py
└── fixtures/                # Test-Daten
    └── sample_files/
```

### Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def temp_dir(tmp_path):
    """Temporäres Verzeichnis für Tests"""
    return tmp_path

@pytest.fixture
def sample_file(temp_dir):
    """Erstellt Test-Datei"""
    file = temp_dir / "test.txt"
    file.write_text("Test-Inhalt")
    return file

@pytest.fixture
def encryptor():
    """Encryptor mit Test-Passwort"""
    from src.core.encryptor import Encryptor
    return Encryptor(password="test123")
```

### Test-Beispiele

**Unit-Test:**
```python
# tests/unit/test_encryptor.py
import pytest
from src.core.encryptor import Encryptor

class TestEncryptor:
    def test_encrypt_decrypt_roundtrip(self, temp_dir):
        # Arrange
        enc = Encryptor("password")
        original = b"Geheime Daten" * 1000

        encrypted_file = temp_dir / "encrypted"
        decrypted_file = temp_dir / "decrypted"

        # Act
        with open(temp_dir / "original", "wb") as f:
            f.write(original)

        with open(temp_dir / "original", "rb") as src:
            with open(encrypted_file, "wb") as dst:
                enc.encrypt_stream(src, dst)

        with open(encrypted_file, "rb") as src:
            with open(decrypted_file, "wb") as dst:
                enc.decrypt_stream(src, dst)

        # Assert
        with open(decrypted_file, "rb") as f:
            decrypted = f.read()

        assert decrypted == original
```

**Integration-Test:**
```python
# tests/integration/test_full_backup.py
import pytest

@pytest.mark.integration
def test_complete_backup_restore_cycle(temp_dir):
    """Voller Backup → Restore Durchlauf"""
    # Setup
    source_dir = temp_dir / "source"
    backup_dir = temp_dir / "backup"
    restore_dir = temp_dir / "restore"

    # Erstelle Test-Dateien
    (source_dir / "file1.txt").write_text("Inhalt 1")
    (source_dir / "file2.txt").write_text("Inhalt 2")

    # Backup
    engine = BackupEngine(...)
    result = engine.create_full_backup([source_dir], None)
    assert result.success

    # Restore
    restore_engine = RestoreEngine(...)
    restore_engine.restore_backup(result.backup_id, restore_dir)

    # Verify
    assert (restore_dir / "file1.txt").read_text() == "Inhalt 1"
    assert (restore_dir / "file2.txt").read_text() == "Inhalt 2"
```

### Mocking

```python
from unittest.mock import Mock, MagicMock

def test_backup_with_mocked_storage():
    # Mock Storage
    mock_storage = Mock(spec=StorageBackend)
    mock_storage.upload_file.return_value = True

    # Use in BackupEngine
    engine = BackupEngine(
        scanner=scanner,
        compressor=compressor,
        encryptor=encryptor,
        storage=mock_storage,  # Mocked!
        metadata=metadata
    )

    # Test
    result = engine.create_full_backup([...], None)

    # Verify Mock wurde aufgerufen
    assert mock_storage.upload_file.called
```

---

## Debugging

### Logging aktivieren

```python
# In main.py oder Test
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Breakpoints

```python
# Mit debugger
import pdb; pdb.set_trace()

# Oder in IDE: Breakpoint setzen
```

### PyQt6 Debugging

```bash
# Qt-Warnings anzeigen
export QT_DEBUG_PLUGINS=1
python src/main.py
```

---

## Best Practices

### 1. Dependency Injection

```python
# ✅ Gut - Testbar
class BackupEngine:
    def __init__(self, storage: StorageBackend, encryptor: Encryptor):
        self.storage = storage
        self.encryptor = encryptor

# ❌ Schlecht - Nicht testbar
class BackupEngine:
    def __init__(self):
        self.storage = USBStorage()  # Hardcoded!
```

### 2. Error Handling

```python
# ✅ Gut
try:
    result = storage.upload_file(file, remote)
except ConnectionError as e:
    logger.error(f"Upload fehlgeschlagen: {e}")
    raise BackupError(f"Verbindung zu Storage verloren") from e

# ❌ Schlecht
try:
    result = storage.upload_file(file, remote)
except:
    pass  # Fehler verschluckt!
```

### 3. Resource Management

```python
# ✅ Gut
with open(file, 'rb') as f:
    data = f.read()

# ❌ Schlecht
f = open(file, 'rb')
data = f.read()
# Datei bleibt offen!
```

### 4. Progress Reporting

```python
# ✅ Gut - Callback für Flexibilität
def process_files(files, progress_callback=None):
    for i, file in enumerate(files):
        process(file)
        if progress_callback:
            progress_callback(i / len(files) * 100)

# ❌ Schlecht - Print direkt
def process_files(files):
    for file in files:
        print(f"Processing {file}")  # Nicht testbar!
```

---

**Viel Erfolg beim Entwickeln! 🚀**

Bei Fragen: [GitHub Discussions](https://github.com/your-username/scrat-backup/discussions)
