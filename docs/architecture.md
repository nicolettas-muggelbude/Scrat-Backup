# Scrat-Backup - Architektur-Dokumentation

Diese Dokumentation beschreibt die technische Architektur von Scrat-Backup.

## Überblick

Scrat-Backup folgt einer **Schichtenarchitektur** mit klarer Trennung zwischen GUI, Business Logic und Datenzugriff.

---

## Architektur-Diagramm

```
┌──────────────────────────────────────────────────────────────┐
│                     GUI LAYER (PyQt6)                         │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐         │
│  │ MainWindow  │  │  Wizard      │  │ Settings    │         │
│  │             │  │              │  │             │         │
│  │ ├─Backup    │  │ ├─Step 1     │  │ ├─Sources   │         │
│  │ ├─Restore   │  │ ├─Step 2     │  │ ├─Destin.   │         │
│  │ ├─History   │  │ └─Step 3     │  │ └─Schedule  │         │
│  │ └─Settings  │  └──────────────┘  └─────────────┘         │
│  └─────────────┘                                              │
└────────────┬─────────────────────────────────────────────────┘
             │ QThread + Signals
             │
┌────────────▼─────────────────────────────────────────────────┐
│                  APPLICATION LAYER                            │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Event Bus (Singleton)                     │  │
│  │  • backup_started                                      │  │
│  │  • backup_progress                                     │  │
│  │  • backup_completed                                    │  │
│  │  • restore_started                                     │  │
│  │  • config_changed                                      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │ BackupWorker  │  │ RestoreWorker  │  │ ScheduleWorker │  │
│  │  (QThread)    │  │   (QThread)    │  │   (QThread)    │  │
│  └───────┬───────┘  └────────┬───────┘  └────────┬───────┘  │
└──────────┼──────────────────┼──────────────────┼────────────┘
           │                  │                  │
           │ Delegates to     │                  │
           │                  │                  │
┌──────────▼──────────────────▼──────────────────▼────────────┐
│                    CORE BUSINESS LOGIC                        │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ BackupEngine │  │RestoreEngine │  │   Scanner    │       │
│  │              │  │              │  │              │       │
│  │ • Full       │  │ • File       │  │ • Scan       │       │
│  │ • Incremental│  │ • Partial    │  │ • Changes    │       │
│  │ • Versioning │  │ • Verify     │  │ • Exclude    │       │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘       │
│         │                 │                                   │
│  ┌──────▼─────────────────▼────────────────────────────────┐ │
│  │              Metadata Manager (SQLite)                  │ │
│  │  • Backup Records     • File Index                      │ │
│  │  • Version Tracking   • Search                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Encryptor   │  │  Compressor  │  │  Scheduler   │       │
│  │              │  │              │  │              │       │
│  │ • AES-256-GCM│  │ • 7z         │  │ • Tasks      │       │
│  │ • PBKDF2     │  │ • Streaming  │  │ • Triggers   │       │
│  │ • Streaming  │  │ • Split      │  │ • Missed     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────┬─────────────────────────────────────────────────┘
             │ StorageBackend Interface
             │
┌────────────▼─────────────────────────────────────────────────┐
│              STORAGE ABSTRACTION LAYER                        │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐│
│  │          StorageBackend (Abstract Base Class)            ││
│  │                                                           ││
│  │  • connect()            • upload_file()                  ││
│  │  • disconnect()         • download_file()                ││
│  │  • list_files()         • delete_file()                  ││
│  │  • get_available_space()                                 ││
│  └──────────────────────────────────────────────────────────┘│
│                             ▲                                 │
│                             │ implements                      │
│      ┌──────────┬───────────┼───────────┬──────────┐         │
│      │          │            │           │          │         │
│  ┌───▼────┐ ┌──▼──────┐ ┌──▼──────┐ ┌──▼──────┐ ┌─▼──────┐  │
│  │  USB   │ │  SFTP   │ │ WebDAV  │ │ Rclone  │ │ Custom │  │
│  │Storage │ │ Storage │ │ Storage │ │ Storage │ │ Plugin │  │
│  └────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## Datenmodelle

### SQLite Schema

```sql
-- Backup-Versionen
CREATE TABLE backups (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    type TEXT,                    -- 'full' | 'incremental'
    base_backup_id INTEGER,       -- NULL für Full, sonst Referenz
    destination_type TEXT,        -- 'usb' | 'sftp' | ...
    destination_path TEXT,
    status TEXT,                  -- 'running' | 'completed' | 'failed'
    files_total INTEGER,
    files_processed INTEGER,
    size_original INTEGER,        -- Bytes
    size_compressed INTEGER,      -- Bytes
    encryption_key_hash TEXT,     -- Zur Passwort-Verifikation
    FOREIGN KEY (base_backup_id) REFERENCES backups(id)
);

-- Dateien in Backups
CREATE TABLE backup_files (
    id INTEGER PRIMARY KEY,
    backup_id INTEGER,
    source_path TEXT,             -- Original-Pfad
    relative_path TEXT,           -- Relativer Pfad
    file_size INTEGER,
    modified_timestamp DATETIME,
    archive_name TEXT,            -- z.B. "data.001.7z"
    archive_path TEXT,            -- Pfad im Archiv
    is_deleted BOOLEAN,           -- Für incremental
    FOREIGN KEY (backup_id) REFERENCES backups(id) ON DELETE CASCADE
);

-- Indizes für Performance
CREATE INDEX idx_backup_files_backup_id ON backup_files(backup_id);
CREATE INDEX idx_backup_files_source_path ON backup_files(source_path);
CREATE INDEX idx_backups_timestamp ON backups(timestamp);
```

### Dataclasses

```python
# models/backup_job.py
from dataclasses import dataclass
from pathlib import Path
from typing import List
from datetime import datetime

@dataclass
class BackupJob:
    """Beschreibt einen Backup-Auftrag"""
    sources: List[Path]
    destination: 'StorageBackend'
    type: str  # 'full' | 'incremental'
    base_backup_id: Optional[int] = None
    encryption_password: str = ""
    compression_level: int = 5

@dataclass
class BackupProgress:
    """Progress-Information für GUI"""
    backup_id: str
    total_files: int
    processed_files: int
    total_bytes: int
    processed_bytes: int
    current_file: str
    speed_mbps: float
    estimated_remaining_seconds: int

@dataclass
class BackupResult:
    """Ergebnis eines Backups"""
    success: bool
    backup_id: int
    files_backed_up: int
    bytes_original: int
    bytes_compressed: int
    duration_seconds: float
    errors: List[str]
```

---

## Backup-Format auf dem Ziel

```
/BackupZiel/scrat-backup/
│
├── metadata.db.enc                 # Verschlüsselte SQLite-DB
│
├── backups/
│   ├── 20250127_220015_full/      # Backup-ID (Timestamp + Typ)
│   │   ├── manifest.json.enc       # Metadaten (verschlüsselt)
│   │   ├── data.001.7z.enc         # Archive (verschlüsselt)
│   │   ├── data.002.7z.enc
│   │   └── data.003.7z.enc
│   │
│   ├── 20250128_220015_incr/      # Inkrementelles Backup
│   │   ├── manifest.json.enc
│   │   └── data.001.7z.enc
│   │
│   └── 20250129_220015_incr/
│       ├── manifest.json.enc
│       └── data.001.7z.enc
│
└── recovery_info.txt               # Unverschlüsselt! Wiederherstellungs-Info
```

### manifest.json Struktur

```json
{
  "backup_id": "20250127_220015_full",
  "type": "full",
  "timestamp": "2025-01-27T22:00:15Z",
  "base_backup": null,
  "sources": [
    {"name": "Dokumente", "path": "C:\\Users\\Nicole\\Documents"},
    {"name": "Bilder", "path": "C:\\Users\\Nicole\\Pictures"}
  ],
  "archives": [
    {
      "name": "data.001.7z.enc",
      "size": 524288000,
      "salt": "base64_encoded_salt",
      "iv": "base64_encoded_iv",
      "auth_tag": "base64_encoded_tag",
      "files_count": 1523
    }
  ],
  "stats": {
    "files_total": 5432,
    "size_original": 15728640000,
    "size_compressed": 10485760000,
    "duration_seconds": 720.5
  }
}
```

### Verschlüsseltes Datei-Format

```
┌─────────────────────────────────────────┐
│ Salt (32 Bytes)                         │  Für PBKDF2
├─────────────────────────────────────────┤
│ IV (16 Bytes)                           │  Initialization Vector
├─────────────────────────────────────────┤
│ Encrypted Data (variabel)               │  AES-256-GCM verschlüsselt
│                                         │
│ ...                                     │
│                                         │
├─────────────────────────────────────────┤
│ Auth Tag (16 Bytes)                     │  GCM Authentication Tag
└─────────────────────────────────────────┘
```

---

## Verschlüsselungs-Architektur

### Master-Key-Ableitung

```
User-Passwort (min. 12 Zeichen)
    │
    ▼
PBKDF2-HMAC-SHA256
├─ Iterations: 100.000
├─ Salt: 32 Bytes (random)
└─ Output: 32 Bytes (256 Bit)
    │
    ▼
Master Key (256 Bit)
    │
    ├─→ Database Encryption Key
    ├─→ Archive Encryption Key
    └─→ Metadata Encryption Key
```

### AES-256-GCM Verschlüsselung

**Eigenschaften:**
- **Mode:** GCM (Galois/Counter Mode)
- **Authenticated Encryption:** Schutz gegen Manipulation
- **Key Size:** 256 Bit
- **IV Size:** 128 Bit (zufällig für jede Verschlüsselung)
- **Auth Tag:** 128 Bit

**Vorteile von GCM:**
- Integrität + Vertraulichkeit in einem
- Performant (parallelisierbar)
- NIST-zugelassen

### Streaming-Verschlüsselung

Für große Dateien (>100MB):

```python
# Pseudo-Code
CHUNK_SIZE = 8 * 1024 * 1024  # 8MB

encryptor = Cipher(
    algorithm=AES(key),
    mode=GCM(iv),
    backend=default_backend()
).encryptor()

# Stream-basiert
while chunk := input_file.read(CHUNK_SIZE):
    encrypted_chunk = encryptor.update(chunk)
    output_file.write(encrypted_chunk)

# Finalize mit Auth-Tag
output_file.write(encryptor.finalize())
output_file.write(encryptor.tag)
```

**Vorteil:** Konstanter RAM-Verbrauch, unabhängig von Dateigröße

---

## Komprimierungs-Architektur

### 7z-Format

**Warum 7z?**
- Bessere Kompression als ZIP
- Native AES-256-Unterstützung (nutzen wir nicht, da wir selbst verschlüsseln)
- Multi-Threading-Unterstützung
- Solid-Archive (optional)

**Konfiguration:**
```python
{
    "compression_level": 5,      # 0-9 (Balance: Speed/Ratio)
    "solid_mode": False,         # Für besseres Streaming
    "split_size_mb": 500,        # Archive bei 500MB splitten
    "threads": 4                 # CPU-Kerne nutzen
}
```

### Split-Archive

Große Backups werden in 500MB-Chunks aufgeteilt:

```
data.001.7z  (500 MB)
data.002.7z  (500 MB)
data.003.7z  (500 MB)
data.004.7z  (237 MB)  # Rest
```

**Vorteile:**
- Bessere Fehlertoleranz (1 Chunk korrupt ≠ alles verloren)
- Granulare Fortschrittsanzeige
- Netzwerk-freundlich (kleinere Transfers)
- Schnelleres Restore einzelner Dateien

---

## Threading-Architektur

### GUI-Thread vs. Worker-Threads

```
┌─────────────────────────────────────────┐
│         Main Thread (GUI)                │
│  • Event Loop                            │
│  • UI Updates                            │
│  • User Input                            │
└────────┬────────────────────────────────┘
         │
         │ Signal/Slot
         │
┌────────▼────────────────────────────────┐
│      BackupWorker (QThread)              │
│  • run() in separatem Thread            │
│  • Emits Signals für Progress           │
│  • Keine direkte GUI-Manipulation       │
└────────┬────────────────────────────────┘
         │
         │ Delegates to
         │
┌────────▼────────────────────────────────┐
│      BackupEngine                        │
│  • Synchroner Code                       │
│  • Progress via Callbacks                │
└──────────────────────────────────────────┘
```

**Wichtig:**
- Nur Main-Thread darf GUI manipulieren!
- Worker kommuniziert via Signals
- Keine Shared State ohne Locks

### Thread-Pool für Datei-Verarbeitung

```python
from concurrent.futures import ThreadPoolExecutor

def process_files(files):
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Parallel: Lesen, Komprimieren, Verschlüsseln
        futures = [
            executor.submit(process_file, file)
            for file in files
        ]

        for future in as_completed(futures):
            result = future.result()
            # Update Progress
```

**Vorsicht:** Nicht zu viele Threads (I/O-Bottleneck)

---

## Event-Driven Architecture

### Event-Bus Pattern

```python
# Singleton Event-Bus
class EventBus(QObject):
    # Backup Events
    backup_started = pyqtSignal(str)              # backup_id
    backup_progress = pyqtSignal(str, int, str)   # id, %, file
    backup_completed = pyqtSignal(str, dict)      # id, stats
    backup_failed = pyqtSignal(str, Exception)

    # Restore Events
    restore_started = pyqtSignal(str)
    restore_progress = pyqtSignal(str, int)
    restore_completed = pyqtSignal(str)

    # Config Events
    config_changed = pyqtSignal(dict)
    storage_connected = pyqtSignal(str)

# Global Instance
event_bus = EventBus()
```

**Nutzung:**

```python
# Emitter (BackupWorker)
event_bus.backup_started.emit(backup_id)
event_bus.backup_progress.emit(backup_id, 50, "file.txt")

# Receiver (MainWindow)
event_bus.backup_progress.connect(self.update_progress_bar)
event_bus.backup_completed.connect(self.show_success_notification)
```

**Vorteile:**
- Lose Kopplung
- Mehrere Listener möglich
- Einfaches Testing (Mock Event-Bus)

---

## Performance-Überlegungen

### 1. Streaming statt Laden

```python
# ✅ Gut - Konstanter RAM
def process_large_file(file):
    with open(file, 'rb') as f:
        while chunk := f.read(8 * 1024 * 1024):
            process_chunk(chunk)

# ❌ Schlecht - RAM = Dateigröße
def process_large_file(file):
    data = file.read()  # Ganze Datei im RAM!
    process(data)
```

### 2. Datenbank-Indizes

```sql
-- Wichtig für schnelle Suche
CREATE INDEX idx_backup_files_source_path ON backup_files(source_path);

-- Ohne Index: O(n) Scan
-- Mit Index: O(log n) Lookup
```

### 3. Batch-Operationen

```python
# ✅ Gut - Batch Insert
cursor.executemany(
    "INSERT INTO backup_files VALUES (?, ?, ?)",
    file_data
)

# ❌ Schlecht - Einzeln
for file in files:
    cursor.execute("INSERT INTO backup_files VALUES (?, ?, ?)", file)
```

### 4. Progress-Update-Throttling

```python
# ✅ Gut - Nicht bei jedem Byte
last_update = 0
def update_progress(bytes_processed):
    global last_update
    now = time.time()
    if now - last_update > 0.1:  # Max 10 Updates/Sekunde
        emit_progress(bytes_processed)
        last_update = now

# ❌ Schlecht - Tausende Updates/Sekunde
def update_progress(bytes_processed):
    emit_progress(bytes_processed)  # Laggt GUI!
```

---

## Sicherheits-Architektur

### Defense in Depth

```
Layer 1: Verschlüsselung
├─ AES-256-GCM (State-of-the-Art)
├─ Zufällige IVs
└─ Authenticated Encryption (kein Tampering)

Layer 2: Key-Derivation
├─ PBKDF2 (100.000 Iterationen)
├─ Zufällige Salts
└─ Kein Klartext-Passwort-Speicherung

Layer 3: Netzwerk-Sicherheit
├─ SFTP: SSH-Verschlüsselung
├─ WebDAV: HTTPS-Pflicht
└─ Zertifikats-Validierung

Layer 4: Daten-Integrität
├─ GCM Auth-Tags
├─ Checksummen in Manifest
└─ Verify-After-Backup

Layer 5: Access Control
├─ Windows Credential Manager (optional)
├─ DPAPI-Verschlüsselung
└─ User-spezifischer Zugriff
```

---

## Erweiterbarkeit

### Plugin-System für Storage-Backends

```python
# 1. Interface definieren (base.py)
class StorageBackend(ABC):
    @abstractmethod
    def upload_file(...): ...

# 2. Plugin implementieren
class MyCloudStorage(StorageBackend):
    def upload_file(self, ...):
        # Custom Implementierung
        ...

# 3. Registrieren
from src.storage.my_cloud import MyCloudStorage

STORAGE_BACKENDS = {
    "usb": USBStorage,
    "sftp": SFTPStorage,
    "mycloud": MyCloudStorage,  # ← Neues Backend
}
```

### Future: Hook-System

```python
# Geplant für v2.0
@hook("before_backup")
def my_pre_backup_script():
    # Custom Code vor Backup
    ...

@hook("after_backup")
def my_post_backup_script(result):
    # Custom Code nach Backup
    if result.success:
        send_notification()
```

---

## Referenzen

- **AES-GCM:** [NIST SP 800-38D](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
- **PBKDF2:** [RFC 8018](https://tools.ietf.org/html/rfc8018)
- **7z Format:** [7-Zip Documentation](https://www.7-zip.org/7z.html)
- **PyQt6:** [Qt Documentation](https://doc.qt.io/qt-6/)

---

**Letzte Aktualisierung:** 2025-01-27
**Version:** 0.1.0-dev
