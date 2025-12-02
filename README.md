<div align="center">

<img src="assets/icons/scrat-256.png" alt="Scrat-Backup Logo" width="128"/>

# 🐿️ Scrat-Backup

**Schütze deine Daten wie Scrat seine Eicheln!**

*Ein benutzerfreundliches, verschlüsseltes Backup-Programm für Windows-Privatnutzer*

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Development Status](https://img.shields.io/badge/status-pre--release%20(v0.1.0--dev)-orange)](https://github.com/your-username/scrat-backup)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)](https://www.microsoft.com/windows)

[Features](#-features) •
[Installation](#-installation) •
[Verwendung](#-verwendung) •
[Entwicklung](#-entwicklung) •
[Roadmap](#-roadmap) •
[Beitragen](#-beitragen)

</div>

---

## 📋 Übersicht

**Scrat-Backup** ist ein **Open-Source-Backup-Tool**, das speziell für **Windows-Privatnutzer** entwickelt wurde. Wie ein Eichhörnchen seine Eicheln für den Winter sichert, schützt Scrat-Backup deine wertvollen Daten mit **verschlüsselten, komprimierten Backups**.

### 🎯 Für wen ist Scrat-Backup?

- 👨‍💼 **Privatnutzer** ohne tiefe technische Kenntnisse
- 🏠 **Heimanwender** mit wichtigen Dokumenten, Fotos, Videos
- 🔒 **Sicherheitsbewusste** die Verschlüsselung schätzen
- 💾 **Multi-Storage-Nutzer** (USB, NAS, Cloud)

---

## ✨ Features

### 🔐 Sicherheit
- ✅ **AES-256-GCM Verschlüsselung** für alle Backups (Pflicht!)
- ✅ **PBKDF2** Key-Derivation (100.000 Iterationen)
- ✅ **Windows Credential Manager** Integration (Passwort speichern)
- ✅ **Kein Plaintext** - sensible Daten immer verschlüsselt

### 💾 Backup-Funktionen
- ✅ **Vollbackups** und **Inkrementelle Backups**
- ✅ **Versionierung** (3 Versionen, konfigurierbar)
- ✅ **Automatische Rotation** alter Backups
- ✅ **Komprimierung** mit 7z (effizient & schnell)
- ✅ **Exclude-Patterns** (z.B. *.tmp, node_modules/)
- ✅ **Progress-Tracking** mit Speed (MB/s) und ETA

### 🗄️ Storage-Backends (5 Optionen!)
- 💾 **USB / Lokale Laufwerke** - mit automatischer Laufwerk-Erkennung
- 🌐 **SFTP (SSH)** - für Remote-Server
- ☁️ **WebDAV** - Nextcloud, ownCloud, SharePoint
- 🚀 **Rclone** - 40+ Cloud-Provider (Google Drive, Dropbox, OneDrive, S3, etc.)
- 🏢 **SMB/CIFS** - Windows-Netzwerkfreigaben, NAS-Geräte

### 🔄 Wiederherstellung
- ✅ **Einzelne Dateien** oder **komplette Backups**
- ✅ **Zeitpunkt-Wiederherstellung** (Version wählen)
- ✅ **Vorschau** der Backup-Inhalte
- ✅ **Wiederherstellung auf beliebigen Systemen** (unabhängig vom Original-User)

### 🖥️ Benutzeroberfläche
- ✅ **Windows 11-Stil GUI** (PyQt6)
- ✅ **Setup-Wizard** für Erstkonfiguration (komplett auf Deutsch!)
  - Persönliche Ordner (Dokumente, Bilder, Musik, Videos, Desktop, Downloads)
  - Automatische Laufwerk-Erkennung
  - Alle 5 Storage-Backends integriert
- ✅ **Backup-Tab** mit Quellen/Ziele-Auswahl
- ✅ **Restore-Tab** mit Backup-Details
- ✅ **Settings-Tab** mit umfassenden Konfigurationen
- ✅ **Logs-Tab** für Fehlersuche

### ⏰ Automatisierung
- ✅ **Zeitpläne** (Täglich, Wöchentlich, Monatlich)
- ✅ **Automatische Backups** beim Start/Herunterfahren (geplant)
- ✅ **System Tray** Integration (geplant)

---

## 🚀 Status

**Aktuell: Phase 11 - Polishing (Pre-Release v0.1.0-dev)**

### ✅ Abgeschlossen
- [x] **Phase 1-5:** Core-Module (Backup/Restore-Engine, Verschlüsselung, Komprimierung)
- [x] **Phase 6-9:** GUI (Hauptfenster, Wizard, Settings, Tabs)
- [x] **Phase 10:** Storage-Backends (alle 5 implementiert!)
- [x] **Phase 11:** Polishing
  - Passwort-Management mit Windows Credential Manager
  - UI-Verbesserungen (Backup/Restore-Tabs)
  - Input-Validierung & Error-Handling
  - Setup-Wizard komplett überarbeitet (Deutsch, Auto-Erkennung)

### 🔨 In Arbeit
- [ ] Hilfefunktion / Guided Tour
- [ ] Barrierefreiheit (Tastatur-Navigation, Screen-Reader)
- [ ] Internationalisierung (Deutsch, Englisch, weitere Sprachen)
- [ ] Dark Mode
- [ ] Update-Funktion

### 📅 Geplant (siehe [TODO.md](TODO.md))
- [ ] **Phase 12:** Release 1.0
  - Windows Installer (.exe)
  - Dokumentation
  - Marketing & Community

**Nächster Meilenstein:** Beta-Version Q1 2025 🎯

---

## 📦 Installation

### Für Endnutzer

**Noch nicht verfügbar - Projekt in Pre-Release-Phase**

Geplant für Release 1.0:
```bash
# Windows Installer
scrat-backup-setup-1.0.exe
```

### Für Entwickler

```bash
# Repository klonen
git clone https://github.com/your-username/scrat-backup.git
cd scrat-backup

# Virtual Environment erstellen
python -m venv venv

# Aktivieren (Windows)
venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt

# Tests ausführen
pytest tests/ -v

# Code-Quality-Checks
./dev.sh check

# Programm starten
python src/main.py
```

---

## 🎮 Verwendung

### Erste Schritte

1. **Setup-Wizard** wird beim ersten Start automatisch geöffnet
2. **Backup-Quellen** wählen (Persönliche Ordner: Dokumente, Bilder, etc.)
3. **Backup-Ziel** auswählen (USB, Cloud, NAS, etc.)
4. **Verschlüsselungs-Passwort** festlegen
5. **Zeitplan** konfigurieren (optional)
6. **Fertig!** Erstes Backup erstellen

### Backup erstellen

```
GUI → Backup-Tab → Quellen wählen → Ziel wählen → "Backup starten"
```

### Dateien wiederherstellen

```
GUI → Restore-Tab → Backup auswählen → Dateien wählen → "Wiederherstellen"
```

---

## 🛠️ Technologie-Stack

| Komponente | Technologie | Version |
|------------|-------------|---------|
| **Sprache** | Python | 3.12+ |
| **GUI** | PyQt6 | 6.10.0 |
| **Verschlüsselung** | cryptography (AES-256-GCM) | 46.0.3 |
| **Komprimierung** | py7zr | 1.0.0 |
| **Datenbank** | SQLite | (built-in) |
| **SFTP** | paramiko | 4.0.0 |
| **WebDAV** | webdavclient3 | 3.14.6 |
| **SMB** | smbprotocol | 1.14.0 |
| **Testing** | pytest | 9.0.1 |

---

## 🔧 Entwicklung

### Projektstruktur

```
scrat-backup/
├── src/
│   ├── main.py                 # Entry Point
│   ├── gui/                    # GUI-Komponenten
│   │   ├── main_window.py      # Hauptfenster
│   │   ├── wizard.py           # Setup-Wizard
│   │   ├── backup_tab.py       # Backup-Tab
│   │   ├── restore_tab.py      # Restore-Tab
│   │   ├── settings_tab.py     # Settings-Tab
│   │   └── ...
│   ├── core/                   # Core-Module
│   │   ├── backup_engine.py    # Backup-Logik
│   │   ├── restore_engine.py   # Restore-Logik
│   │   ├── encryptor.py        # Verschlüsselung
│   │   ├── compressor.py       # Komprimierung
│   │   └── ...
│   ├── storage/                # Storage-Backends
│   │   ├── usb_storage.py      # USB/Lokal
│   │   ├── sftp_storage.py     # SFTP
│   │   ├── webdav_storage.py   # WebDAV
│   │   ├── rclone_storage.py   # Rclone
│   │   └── smb_storage.py      # SMB/CIFS
│   └── utils/                  # Utilities
├── tests/                      # 121 Tests (>80% Coverage)
├── docs/                       # Dokumentation
│   ├── developer_guide.md
│   └── architecture.md
├── assets/                     # Icons, Themes
├── TODO.md                     # Roadmap
└── claude.md                   # Technische Dokumentation
```

### Code-Quality

```bash
# Alle Checks
./dev.sh check

# Nur Formatierung
./dev.sh format

# Nur Tests
./dev.sh test
```

**Standards:**
- ✅ **PEP 8** Coding Style
- ✅ **Type Hints** für alle Funktionen
- ✅ **Docstrings** (Google Style)
- ✅ **>80% Test Coverage**

---

## 📖 Dokumentation

| Dokument | Beschreibung |
|----------|--------------|
| [claude.md](claude.md) | Vollständige technische Dokumentation |
| [TODO.md](TODO.md) | Roadmap & geplante Features |
| [docs/developer_guide.md](docs/developer_guide.md) | Entwickler-Handbuch |
| [docs/architecture.md](docs/architecture.md) | Architektur-Übersicht |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Beitrags-Richtlinien |

---

## 🗺️ Roadmap

Siehe [TODO.md](TODO.md) für die vollständige Roadmap.

### Vor Release 1.0

**Priorität: Hoch**
- [ ] Hilfefunktion / Guided Tour
- [ ] Barrierefreiheit (A11y)
- [ ] Internationalisierung (i18n)
- [ ] Dark Mode
- [ ] Farbenblindheit-freundliche Farben

**Priorität: Mittel**
- [ ] Update-Funktion
- [ ] Vollständige Test-Coverage
- [ ] Performance-Optimierungen

**Nach dem Release**
- [ ] Projektwebseite
- [ ] Social Media Content
- [ ] Community aufbauen

---

## 🤝 Beitragen

Contributions sind herzlich willkommen! 🎉

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add: AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

### Contributors

<!-- ALL-CONTRIBUTORS-LIST:START -->
Noch keine Contributors - sei der Erste! 🚀
<!-- ALL-CONTRIBUTORS-LIST:END -->

---

## 📄 Lizenz

**GNU General Public License v3.0**

Dieses Projekt ist **Open-Source** und unter der GPLv3 lizenziert.
Siehe [LICENSE](LICENSE) für Details.

### Verwendete Bibliotheken

| Bibliothek | Lizenz | Kompatibel? |
|------------|--------|-------------|
| PyQt6 | GPL / Commercial | ✅ GPL |
| cryptography | Apache 2.0 / BSD | ✅ Ja |
| py7zr | LGPL | ✅ Ja |
| paramiko | LGPL | ✅ Ja |
| webdavclient3 | MIT | ✅ Ja |
| smbprotocol | MIT | ✅ Ja |

Alle Dependencies sind **GPLv3-kompatibel**.

---

## 🔐 Sicherheit

Scrat-Backup nimmt **Sicherheit ernst**:

- 🔒 **AES-256-GCM**: Authenticated Encryption für alle Backups
- 🔑 **PBKDF2**: 100.000 Iterationen für Key-Derivation
- 🚫 **Kein Plaintext**: Alle sensiblen Daten verschlüsselt
- 💾 **Windows Credential Manager**: Optionale Passwort-Speicherung

### Sicherheitslücken melden

**Bitte NICHT als öffentliches Issue!**

Sende eine E-Mail an: **security@scrat-backup.example**

---

## 💬 Support

- 📚 **Dokumentation**: [claude.md](claude.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-username/scrat-backup/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/your-username/scrat-backup/discussions)
- ❓ **Fragen**: [GitHub Discussions](https://github.com/your-username/scrat-backup/discussions/categories/q-a)

---

## 🙏 Danksagungen

- **Inspiration**: rsync, duplicati, borg backup
- **Icon**: Eichel 🌰 (Scrat aus Ice Age)
- **Community**: Alle zukünftigen Contributors!
- **Claude Code**: Development-Assistent 🤖

---

## 📊 Statistiken

![Tests](https://img.shields.io/badge/tests-121%20passed-success)
![Coverage](https://img.shields.io/badge/coverage-80%25+-success)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/badge/license-GPLv3-green)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)
![Status](https://img.shields.io/badge/status-pre--release-orange)

---

<div align="center">

**Entwickelt mit ❤️ für die Open-Source-Community**

*Wie ein Eichhörnchen seine Eicheln bewahrt, so bewahren wir deine Daten.* 🐿️🌰

**[⭐ Star das Projekt](https://github.com/your-username/scrat-backup) • [🐛 Report Bug](https://github.com/your-username/scrat-backup/issues) • [💡 Request Feature](https://github.com/your-username/scrat-backup/discussions)**

</div>
