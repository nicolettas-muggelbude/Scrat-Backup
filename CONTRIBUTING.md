# Contributing zu Scrat-Backup 🌰

Danke für dein Interesse, zu Scrat-Backup beizutragen! Wir freuen uns über jede Hilfe.

## 📋 Inhaltsverzeichnis

- [Code of Conduct](#code-of-conduct)
- [Wie kann ich beitragen?](#wie-kann-ich-beitragen)
- [Development Setup](#development-setup)
- [Entwicklungs-Workflow](#entwicklungs-workflow)
- [Coding-Standards](#coding-standards)
- [Testing-Richtlinien](#testing-richtlinien)
- [Commit-Messages](#commit-messages)
- [Pull Request Prozess](#pull-request-prozess)

---

## Code of Conduct

Dieses Projekt folgt den Grundsätzen von Respekt, Inklusivität und konstruktiver Zusammenarbeit.

**Erwartungen:**
- Respektvoller Umgang mit allen Contributors
- Konstruktives Feedback
- Fokus auf das Projekt und seine Ziele
- Keine Diskriminierung jeglicher Art

Bei Verstößen bitte als Issue melden.

---

## Wie kann ich beitragen?

### 🐛 Bugs melden

Bugs bitte als [GitHub Issue](https://github.com/nicolettas-muggelbude/scrat-backup/issues) melden mit:

**Vorlage:**
```markdown
**Beschreibung:**
Kurze Beschreibung des Problems

**Schritte zum Reproduzieren:**
1. Schritt 1
2. Schritt 2
3. ...

**Erwartetes Verhalten:**
Was sollte passieren?

**Tatsächliches Verhalten:**
Was passiert stattdessen?

**Umgebung:**
- OS: [z.B. Windows 11]
- Python-Version: [z.B. 3.12.3]
- Scrat-Backup Version: [z.B. 0.1.0]

**Logs/Screenshots:**
Falls vorhanden
```

### 💡 Features vorschlagen

Feature-Requests als [GitHub Issue](https://github.com/nicolettas-muggelbude/scrat-backup/issues) mit:

- Beschreibung des Features
- Use-Case: Warum ist es nützlich?
- Vorschlag zur Implementierung (optional)
- Mockups/Wireframes (bei GUI-Features)

### 🔧 Code beitragen

1. **Issue finden oder erstellen**
   - Schaue in den [Issues](https://github.com/nicolettas-muggelbude/scrat-backup/issues)
   - Labels: `good first issue`, `help wanted`

2. **Änderungen implementieren**
   - Siehe [Development Setup](#development-setup)
   - Siehe [Entwicklungs-Workflow](#entwicklungs-workflow)

3. **Pull Request erstellen**
   - Siehe [Pull Request Prozess](#pull-request-prozess)

---

## Development Setup

### Voraussetzungen

- **Python 3.10+** (empfohlen: 3.12)
- **Git**
- **Linux, macOS oder Windows** (Entwicklung auf Linux/WSL und Windows)

### Ersteinrichtung

```bash
# Linux (Debian/Ubuntu) – System-Dependencies:
sudo apt install python3.12 python3-pip python3-keyring libsecret-1-0 smbclient \
                 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
                 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0

# Linux (Fedora):
sudo dnf install python3.12 python3-pip python3-keyring libsecret samba-client

# Linux (Arch):
sudo pacman -S python python-pip python-keyring libsecret smbclient

# 1. Repository klonen
git clone https://github.com/nicolettas-muggelbude/Scrat-Backup.git
cd Scrat-Backup

# 2. Virtual Environment erstellen und aktivieren
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. Programm starten
python3 src/main.py

# 5. Code-Quality prüfen (optional, vor erstem Commit)
./dev.sh check
```

### Nützliche Befehle

Das `dev.sh` Script erleichtert die Entwicklung (Linux/macOS):

```bash
./dev.sh help      # Alle verfügbaren Befehle
./dev.sh run       # Programm starten
./dev.sh test      # Tests ausführen (pytest)
./dev.sh coverage  # Tests + Coverage-Report (htmlcov/index.html)
./dev.sh format    # Code automatisch formatieren (black + isort)
./dev.sh check     # Code-Quality: black + isort + flake8 + mypy
./dev.sh lint      # Nur flake8
./dev.sh types     # Nur mypy
./dev.sh clean     # __pycache__, .pyc, .coverage aufräumen
./dev.sh install   # Dependencies neu installieren
```

---

## Entwicklungs-Workflow

### 1. Branch erstellen

```bash
# Feature-Branch
git checkout -b feature/mein-feature

# Bugfix-Branch
git checkout -b bugfix/issue-123

# Dokumentation
git checkout -b docs/improve-readme
```

**Branch-Naming-Konventionen:**
- `feature/` - Neue Features
- `bugfix/` - Bugfixes
- `docs/` - Dokumentation
- `refactor/` - Code-Refactoring
- `test/` - Tests hinzufügen/verbessern

### 2. Entwickeln

```bash
# Code schreiben
# ...

# Regelmäßig formatieren und prüfen
./dev.sh format
./dev.sh check

# Tests schreiben und ausführen
./dev.sh test
```

### 3. Committen

```bash
# Geänderte Dateien stagen
git add src/gui/wizard_v2.py

# Status prüfen
git status

# Commit mit aussagekräftiger Message
git commit -m "feat: Neue Funktion XYZ hinzugefügt"
```

Siehe [Commit-Messages](#commit-messages) für Konventionen.

### 4. Push und Pull Request

```bash
# Branch pushen
git push origin feature/mein-feature

# Pull Request auf GitHub erstellen
# Siehe [Pull Request Prozess](#pull-request-prozess)
```

---

## Coding-Standards

### Python-Style

Wir folgen **PEP 8** mit einigen Anpassungen:

- **Line Length:** 100 Zeichen (nicht 79)
- **Quotes:** Double Quotes `"` bevorzugt
- **Trailing Commas:** Ja, bei multi-line

### Code-Formatierung

**Automatisch mit:**
```bash
./dev.sh format
```

Dies führt aus:
- `black` - Code-Formatter
- `isort` - Import-Sortierer

### Type Hints

**Pflicht für alle öffentlichen Funktionen:**

```python
# ✅ Gut
def backup_file(source: Path, destination: Path) -> bool:
    """Sichert eine Datei."""
    ...

# ❌ Schlecht
def backup_file(source, destination):
    ...
```

**Prüfung mit:**
```bash
./dev.sh types
```

### Docstrings

**Pflicht für alle öffentlichen Klassen/Funktionen:**

```python
def create_backup(sources: List[Path], destination: Path) -> BackupResult:
    """
    Erstellt ein Backup von mehreren Quellen.

    Args:
        sources: Liste von Quell-Pfaden
        destination: Ziel-Pfad für das Backup

    Returns:
        BackupResult mit Status und Metadaten

    Raises:
        BackupError: Wenn Backup fehlschlägt
        PermissionError: Wenn keine Schreibrechte
    """
    ...
```

**Stil:** Google-Style Docstrings

### Imports

**Reihenfolge (automatisch via isort):**

```python
# 1. Standard Library
import sys
from pathlib import Path

# 2. Third-Party
from PySide6.QtWidgets import QMainWindow
import pytest

# 3. Local
from src.core.backup_engine import BackupEngine
from src.utils.credential_manager import get_credential_manager
```

### Fehlerbehandlung

**Spezifische Exceptions:**

```python
# ✅ Gut
try:
    with open(file_path, 'r') as f:
        data = f.read()
except FileNotFoundError:
    logger.error(f"Datei nicht gefunden: {file_path}")
    raise BackupError(f"Quell-Datei fehlt: {file_path}")

# ❌ Schlecht - zu allgemein
try:
    ...
except Exception:
    pass
```

### Logging

**Strukturiert und informativ:**

```python
import logging

logger = logging.getLogger(__name__)

# Levels verwenden
logger.debug("Detaillierte Debug-Info")
logger.info("Backup gestartet für 123 Dateien")
logger.warning("Datei übersprungen: temp.tmp")
logger.error("Backup fehlgeschlagen", exc_info=True)
logger.critical("Datenbank korrupt!")
```

### Kommentare

**Deutsch für Erklärungen, Code spricht für sich:**

```python
# ✅ Gut - Kommentar erklärt WARUM
# Wir müssen hier zweimal prüfen wegen Race-Condition bei NFS
if file.exists() and file.is_file():
    process_file(file)

# ❌ Schlecht - Kommentar wiederholt Code
# Prüfe ob Datei existiert
if file.exists():
    ...
```

---

## Testing-Richtlinien

### Test-Struktur

```
tests/
├── unit/                      # Unit-Tests
│   └── test_*.py
├── test_backup_engine.py      # BackupEngine-Tests
├── test_compressor.py         # Compressor-Tests
├── test_scanner.py            # Scanner-Tests
├── test_config_manager.py     # Config-Tests
├── test_gui.py                # GUI-Tests (pytest-qt)
├── fixtures/                  # Test-Daten
│   └── sample_files/
└── conftest.py                # Pytest-Konfiguration
```

### Tests ausführen

```bash
# Alle Tests
./dev.sh test

# Mit Coverage-Report
./dev.sh coverage
# → Bericht öffnen: htmlcov/index.html

# Einzelne Datei
venv/bin/pytest tests/test_compressor.py -v

# Nur schnelle Tests (ohne langsame Integrations-Tests)
venv/bin/pytest tests/ -m "not slow" -v
```

### Test schreiben

```python
import pytest
from src.core.encryptor import Encryptor


class TestEncryptor:
    """Tests für Encryptor-Klasse"""

    def test_encrypt_decrypt_roundtrip(self):
        """Verschlüsseln und Entschlüsseln ergibt Original"""
        # Arrange
        encryptor = Encryptor(password="TestPasswort123!")
        original_data = b"Geheime Daten"

        # Act
        ciphertext, nonce = encryptor.encrypt_bytes(original_data)
        decrypted = encryptor.decrypt_bytes(ciphertext, nonce)

        # Assert
        assert decrypted == original_data
        assert ciphertext != original_data

    def test_wrong_password_raises_error(self):
        """Falsches Passwort wirft Fehler"""
        from cryptography.exceptions import InvalidTag

        enc1 = Encryptor(password="correct123!")
        enc2 = Encryptor(password="wrong123!", salt=enc1.salt)
        ciphertext, nonce = enc1.encrypt_bytes(b"data")

        with pytest.raises(InvalidTag):
            enc2.decrypt_bytes(ciphertext, nonce)
```

### Test-Coverage

**Ziel: >80%**

```bash
./dev.sh coverage
# Öffne htmlcov/index.html
```

### Test-Markers

```python
@pytest.mark.unit
def test_simple_function():
    ...

@pytest.mark.integration
def test_full_workflow():
    ...

@pytest.mark.slow
def test_large_backup():
    ...
```

**Ausführen:**
```bash
pytest -m unit          # Nur Unit-Tests
pytest -m "not slow"    # Ohne langsame Tests
```

---

## Commit-Messages

Wir folgen [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat:` - Neues Feature
- `fix:` - Bugfix
- `docs:` - Dokumentation
- `style:` - Formatierung (keine Code-Änderung)
- `refactor:` - Code-Refactoring
- `test:` - Tests hinzufügen/ändern
- `chore:` - Build, Dependencies, etc.
- `perf:` - Performance-Verbesserung

### Beispiele

```bash
# Feature
git commit -m "feat(backup): Unterstützung für WebDAV hinzugefügt"

# Bugfix
git commit -m "fix(encryptor): Crash bei leeren Dateien behoben"

# Dokumentation
git commit -m "docs: CONTRIBUTING.md erstellt"

# Mit Body
git commit -m "feat(gui): Dark Mode implementiert

- Theme-Switcher in Settings
- Automatische Erkennung von System-Theme
- Persistente Speicherung der Präferenz

Closes #42"
```

### Regeln

- **Subject:** Max 50 Zeichen, Imperativ ("füge hinzu" nicht "hinzugefügt")
- **Body:** Erkläre WARUM, nicht WAS (das sieht man im Code)
- **Footer:** Referenziere Issues (`Closes #123`, `Fixes #456`)

---

## Pull Request Prozess

### 1. Vorbereitung

**Vor dem PR sicherstellen:**

```bash
# Code formatiert und geprüft
./dev.sh format
./dev.sh check

# Alle Tests bestehen
./dev.sh test

# Branch ist aktuell
git fetch origin
git rebase origin/main
```

### 2. PR erstellen

**Titel:** Wie Commit-Message
```
feat(backup): WebDAV-Unterstützung hinzugefügt
```

**Beschreibung:**

```markdown
## Änderungen
- WebDAV-Storage-Backend implementiert
- Tests für WebDAV hinzugefügt
- Dokumentation aktualisiert

## Motivation
User haben nach WebDAV-Support gefragt (#42)

## Test-Plan
- [x] Unit-Tests für WebDAVStorage
- [x] Integration-Test mit realem WebDAV-Server
- [x] Manueller Test mit Nextcloud

## Screenshots
(falls GUI-Änderungen)

## Checklist
- [x] Code folgt Style-Guide
- [x] Tests geschrieben und bestehen
- [x] Dokumentation aktualisiert
- [x] Keine Breaking Changes (oder dokumentiert)

Closes #42
```

### 3. Review-Prozess

- **Mindestens 1 Approval** erforderlich
- **CI muss grün sein** (alle Tests bestehen)
- Feedback addressieren:
  - Bei kleinen Änderungen: Direkt fixen
  - Bei größeren: Diskutieren in Comments

### 4. Nach Merge

```bash
# Cleanup
git checkout main
git pull origin main
git branch -d feature/mein-feature
```

---

## Projekt-Struktur

```
src/
├── main.py                    # Entry Point
├── gui/                       # PySide6 GUI (Wizard, MainWindow, Tabs)
├── core/                      # Business Logic (BackupEngine, Encryptor, …)
├── templates/
│   ├── handlers/              # Template-Handler (USB, OneDrive, Nextcloud, …)
│   └── *.json                 # Template-Definitionen
└── utils/                     # Hilfsfunktionen (CredentialManager, …)

tests/                         # pytest-Tests
docs/
└── TESTING.md                 # Test-Anleitung
```

**Wichtig:**
- Kein GUI-Code in `core/`
- Keine Business-Logic in `gui/`
- Template-Handler erben von `TemplateHandler` (base.py)

---

## Hilfe bekommen

- **Technische Doku:** [CLAUDE.md](CLAUDE.md) – Architektur, Entscheidungen, Sessions
- **Test-Anleitung:** [docs/TESTING.md](docs/TESTING.md)
- **Issues:** [GitHub Issues](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)
- **Discussions:** [GitHub Discussions](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions)

---

## Lizenz

Mit deinem Beitrag stimmst du zu, dass dein Code unter der **GPLv3** lizenziert wird.

---

**Danke für deinen Beitrag zu Scrat-Backup! 🌰**
