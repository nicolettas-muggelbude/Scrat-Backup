<div align="center">

<img src="assets/icons/scrat-256.png" alt="Scrat-Backup Logo" width="128"/>

# 🐿️ Scrat-Backup

**Schütze deine Daten wie Scrat seine Eicheln!**

*Ein benutzerfreundliches, plattformübergreifendes Backup-Programm mit Verschlüsselung*

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Development Status](https://img.shields.io/badge/status-beta%20(v0.2.0)-yellow)](https://github.com/nicolettas-muggelbude/Scrat-Backup)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)](#)

[Features](#-features) •
[Installation](#-installation) •
[Verwendung](#-verwendung) •
[Entwicklung](#-entwicklung) •
[Roadmap](#-roadmap) •
[Beitragen](#-beitragen)

</div>

---

## 📋 Übersicht

**Scrat-Backup** ist ein **plattformübergreifendes Open-Source-Backup-Tool** für **Privatnutzer**. Wie ein Eichhörnchen seine Eicheln für den Winter sichert, schützt Scrat-Backup deine wertvollen Daten mit **verschlüsselten, komprimierten Backups**.

**Unterstützte Plattformen:**
- 🪟 **Windows** 10/11
- 🐧 **Linux** (alle Distributionen)
- 🍎 **macOS** (10.15+)

### 🎯 Für wen ist Scrat-Backup?

- 👨‍💼 **Privatnutzer** ohne tiefe technische Kenntnisse
- 🏠 **Heimanwender** mit wichtigen Dokumenten, Fotos, Videos
- 🔒 **Sicherheitsbewusste** die Verschlüsselung schätzen
- 💾 **Multi-Storage-Nutzer** (USB, NAS, Cloud)
- 🌍 **Cross-Platform-Nutzer** (gleiche Backups auf allen Systemen)

---

## ✨ Features

### 🔐 Sicherheit
- ✅ **AES-256-GCM Verschlüsselung** für alle Backups (Pflicht!)
- ✅ **PBKDF2** Key-Derivation (100.000 Iterationen)
- ✅ **Sichere Passwort-Speicherung** (Windows Credential Manager, Linux/macOS Keyring)
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
- ✅ **Moderne GUI** mit nativer Optik (PySide6/Qt6)
- ✅ **Setup-Wizard V3** mit Template-System
  - Komplett auf Deutsch mit Qt-Übersetzungen
  - Template-basierte Konfiguration (7 Templates verfügbar)
  - Persönliche Ordner mit automatischer Erkennung
  - **Plattformspezifisch**: Automatische Anpassung an Windows/Linux/macOS
  - Barrierefreie Ordner-Auswahl (Textfeld + Schnellauswahl)
- ✅ **Dark Mode** mit automatischer System-Erkennung (alle Plattformen)
- ✅ **Barrierefreiheit**: Vollständige Tastatur-Navigation im Wizard
- ✅ **Backup-Tab** mit Quellen/Ziele-Auswahl
- ✅ **Restore-Tab** mit Backup-Details
- ✅ **Settings-Tab** mit umfassenden Konfigurationen
- ✅ **Logs-Tab** für Fehlersuche

### ⏰ Automatisierung & Scheduler
- ✅ **Zeitpläne erstellen** (Täglich, Wöchentlich, Monatlich, bei Start/Shutdown)
- ✅ **Scheduler-Worker** läuft im Hintergrund (prüft alle 60 Sekunden)
- ✅ **Automatische Backup-Ausführung** zu geplanten Zeiten
- ✅ **Missed-Backup-Detection** (erkennt verpasste Backups)
- ✅ **"Nächster Lauf"-Anzeige** für jeden Zeitplan
- ✅ **System Tray** Integration mit Notifications
- ✅ **Pause/Resume** für Scheduler

---

## 🚀 Status

**Aktuell: Beta v0.2.0 - Ready for Testing! 🎉**

### ✅ Abgeschlossen
- [x] **Phase 1-5:** Core-Module (Backup/Restore-Engine, Verschlüsselung, Komprimierung)
- [x] **Phase 6-9:** GUI (Hauptfenster, Wizard, Settings, Tabs)
- [x] **Phase 10:** Scheduler & Automatisierung
  - Zeitpläne (Täglich, Wöchentlich, Monatlich)
  - Scheduler-Worker läuft im Hintergrund
  - Missed-Backup-Detection
  - "Nächster Lauf"-Anzeige
  - 22 Scheduler-Tests ✅
- [x] **Phase 11:** Polishing
  - Passwort-Management mit Windows Credential Manager
  - UI-Verbesserungen (Backup/Restore-Tabs)
  - Input-Validierung & Error-Handling
  - Setup-Wizard komplett überarbeitet (Deutsch, Auto-Erkennung)
- [x] **Wizard V3** (2026-02-01/02)
  - Template-System mit 7 Templates (USB, OneDrive, Google Drive, Nextcloud, Dropbox, Synology, QNAP)
  - DynamicTemplateForm mit Handler-Actions
  - Dark Mode mit Auto-Detection
  - Barrierefreiheit: Tastatur-Navigation, Textfeld + Schnellauswahl
  - Einheitliches Design (ohne Frames)
  - Deutsche Qt-Übersetzungen

### 🔨 Phase 12: Packaging & Beta-Release (In Arbeit)
- [x] PyInstaller-Konfiguration
- [x] Build-Script (build_exe.py)
- [x] Inno Setup Installer-Script
- [x] Build-Dokumentation (BUILD.md)
- [ ] Beta-Testing
- [ ] GitHub Release

### 📅 Geplant (siehe [TODO.md](TODO.md))
- [ ] Hilfefunktion / Guided Tour
- [x] Barrierefreiheit: Tastatur-Navigation ✅ (Wizard)
- [ ] Barrierefreiheit: Screen-Reader-Unterstützung (in Arbeit)
- [ ] Internationalisierung (Englisch, weitere Sprachen)
- [x] Dark Mode ✅ (mit Auto-Detection)
- [ ] Restore-Flow im Wizard
- [ ] Update-Funktion
- [ ] Release 1.0 (Q2 2026)

**Aktueller Meilenstein:** Public Beta Testing 🎯

---

## 📦 Installation

### 🎉 Beta-Version verfügbar!

**Download: [Releases](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases)**

#### Windows 10/11

**Variante 1: Portable ZIP (Empfohlen)**
1. Lade `ScratBackup-v0.2.0-beta-windows.zip` herunter
2. Entpacke das ZIP-Archiv
3. Starte `ScratBackup.exe`
4. Folge dem Setup-Wizard

**Variante 2: Installer**
1. Lade `ScratBackup-v0.2.0-beta-Setup.exe` herunter
2. Führe den Installer aus
3. Starte über Startmenü oder Desktop-Icon

#### Linux (alle Distributionen)

```bash
# System-Dependencies installieren
# Debian/Ubuntu:
sudo apt install python3.12 python3-pip python3-keyring libsecret-1-0 smbclient cron \
                 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
                 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0

# Fedora:
sudo dnf install python3.12 python3-pip python3-keyring libsecret samba-client cronie

# Arch:
sudo pacman -S python python-pip python-keyring libsecret smbclient cronie

# Scrat-Backup klonen und installieren
git clone https://github.com/nicolettas-muggelbude/Scrat-Backup.git
cd scrat-backup
pip install -r requirements.txt

# Starten
python3 src/main.py
```

#### macOS (10.15+)

```bash
# Homebrew installieren (falls nicht vorhanden)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.12 installieren
brew install python@3.12

# Scrat-Backup klonen und installieren
git clone https://github.com/nicolettas-muggelbude/Scrat-Backup.git
cd scrat-backup
pip3 install -r requirements.txt

# Starten
python3 src/main.py
```

**⚠️ Beta-Hinweis:** Dies ist eine Testversion. Bitte melde Bugs auf [GitHub Issues](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues).

### Für Entwickler

```bash
# Repository klonen
git clone https://github.com/nicolettas-muggelbude/Scrat-Backup.git
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
├── tests/                      # 143 Tests (>80% Coverage)
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
| [BUILD.md](BUILD.md) | Build-Anleitung für Entwickler |
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
- [x] Barrierefreiheit (A11y) - Tastatur-Navigation ✅
- [ ] Barrierefreiheit - Screen-Reader, Hochkontrast
- [ ] Internationalisierung (i18n)
- [x] Dark Mode ✅
- [ ] Farbenblindheit-freundliche Farben
- [ ] Restore-Flow im Wizard

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
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions)
- ❓ **Fragen**: [GitHub Discussions](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions/categories/q-a)

---

## 🙏 Danksagungen

- **Inspiration**: rsync, duplicati, borg backup
- **Icon**: Eichel 🌰 (Scrat aus Ice Age)
- **Community**: Alle zukünftigen Contributors!
- **Claude Code**: Development-Assistent 🤖

---

## 📊 Statistiken

![Tests](https://img.shields.io/badge/tests-143%20passed-success)
![Coverage](https://img.shields.io/badge/coverage-80%25+-success)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/badge/license-GPLv3-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Status](https://img.shields.io/badge/status-beta%20v0.2.0-yellow)

---

<div align="center">

**Entwickelt mit ❤️ für die Open-Source-Community**

*Wie ein Eichhörnchen seine Eicheln bewahrt, so bewahren wir deine Daten.* 🐿️🌰

**[⭐ Star das Projekt](https://github.com/nicolettas-muggelbude/Scrat-Backup) • [📥 Download Beta](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases) • [🐛 Report Bug](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues) • [💡 Request Feature](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions)**

</div>
