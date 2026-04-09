# 🎉 Scrat-Backup v0.3.15-beta Release Notes

## 💾 Downloads

| Plattform | Download |
|-----------|----------|
| 🪟 **Windows** (x64) | [⬇ ScratBackup-v0.3.15-beta-Setup.exe](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.15-beta/ScratBackup-v0.3.15-beta-Setup.exe) |
| 🐧 **Linux** (x86_64, versioniert) | [⬇ ScratBackup-v0.3.15-beta-x86_64.AppImage](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.15-beta/ScratBackup-v0.3.15-beta-x86_64.AppImage) |
| 🐧 **Linux** (x86_64, neutral) | [⬇ ScratBackup-x86_64.AppImage](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.15-beta/ScratBackup-x86_64.AppImage) |
| 🐧 **Linux** Desktop-Integration | [⬇ install.sh](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.15-beta/install.sh) |

---

## 🐿️ Tray-Menü und automatische Backups repariert!

**Scrat-Backup v0.3.15-beta** behebt zwei kritische Bugs: Das Tray-Menü öffnet jetzt korrekt den Wizard, und automatisch geplante Backups werden nach dem Wizard im Betriebssystem registriert.

**Wie ein Eichhörnchen seine Eicheln immer wiederfindet, so findest du deine Daten jetzt auf jedem Gerät.** 🌰

---

## ✨ Highlights dieser Version

### ⚙️ Tray-Menü öffnet Wizard

Das Tray-Menü war falsch verdrahtet – alle Optionen öffneten das MainWindow (Expertenansicht). Jetzt:

- **Einstellungen** → öffnet den Wizard (Backup einrichten / ändern)
- **Backup starten** → startet Backup direkt
- **Wiederherstellen** → öffnet Wizard auf der Restore-Seite
- **Expertenansicht** (neu) → öffnet das MainWindow für Power-User
- **Beenden** → beendet die App

### 🕐 Automatische Backups funktionieren jetzt

Nach dem Wizard-Abschluss wird der konfigurierte Zeitplan im Betriebssystem registriert:

- **Windows:** Windows Task Scheduler (`schtasks`) – täglich, wöchentlich, monatlich oder beim Start
- **Linux:** crontab – mit korrekt generiertem Cron-Ausdruck

### 🖥️ Headless-Modus (`--backup`)

Für den OS-Scheduler: `ScratBackup.exe --backup` (oder AppImage) startet das Backup ohne GUI:

- Liest Quellen und Ziel aus `config.json`
- Passwort aus Keyring (kein Dialog nötig)
- Vollständiges Backup im Hintergrund

---

## 🔧 Was funktioniert

### Core-Funktionen
- ✅ **Backup-Engine** – Vollbackups und inkrementelle Backups
- ✅ **Restore-Engine** – Einzelne Dateien oder komplette Backups
- ✅ **AES-256-GCM Verschlüsselung** – Alle Backups verschlüsselt (Chunked, 64MB)
- ✅ **zstd-Komprimierung** – ~5–10× schneller als LZMA, Level 1
- ✅ **Versionierung** – Konfigurierbare Rotationsanzahl
- ✅ **metadata.db-Portabilität** – Restore auf beliebigem Gerät

### Storage-Backends
- ✅ **USB / Lokale Laufwerke** (Win + Linux, inkl. externer Festplatten)
- ✅ **SFTP (SSH)** – mit sicherer Host-Key-Prüfung
- ✅ **WebDAV / Nextcloud**
- ✅ **Rclone** (Google Drive, Dropbox, OneDrive, 40+ Provider)
- ✅ **SMB/CIFS** (Synology, QNAP, Windows-Freigaben)

### Wizard
- ✅ **StartPage** – Aktionsauswahl (Backup einrichten / ändern / Restore / Experten-Modus)
- ✅ **SourceSelectionPage** – Quellen mit Bibliotheks-Checkboxen, eigene Ordner, Ausschlüsse
- ✅ **TemplateDestinationPage** – Template-Kacheln, USB-Backup funktioniert
- ✅ **SchedulePage** – Täglich/Wöchentlich/Monatlich/beim Start, Zeitangabe, Wochentag
- ✅ **EncryptionPage** – Passwort + Keyring
- ✅ **RestoreWizardPage** – DB- und Verzeichnis-Modus
- ✅ **FinishPage** – Tray-Start oder Experten-Modus

### System Tray
- ✅ **Einstellungen** → Wizard
- ✅ **Backup starten** → direktes Backup
- ✅ **Wiederherstellen** → Restore-Wizard
- ✅ **Expertenansicht** → MainWindow
- ✅ **Auto-Updater** – tägliche Prüfung, Dialog mit Release Notes

### Zeitplanung
- ✅ **Windows Task Scheduler** – daily/weekly/monthly/startup via schtasks
- ✅ **Linux crontab** – korrekte Cron-Ausdrücke für alle Frequenzen
- ✅ **`--backup` Headless-Modus** – für OS-Scheduler-Aufrufe ohne GUI

### Dark Mode
- ✅ Auto-Detection + manuelles Umschalten
- ✅ Alle Wizard-Seiten theme-aware

---

## ⚠️ Bekannte Limitierungen (Beta)

- ❌ **macOS-Build** – noch kein macOS-Runner in CI
- ❌ **Internationalisierung** – aktuell nur Deutsch
- ❌ **Template-Manager-Tab** im MainWindow noch nicht implementiert
- ⚠️ **SFTP:** Unbekannte Hosts werden abgelehnt – vorher `ssh user@host` ausführen (einmalig)
- ⚠️ **Upgrade von älteren Versionen (Windows):** Config-Pfad hat sich geändert – alte Config von `%USERPROFILE%\.scrat-backup\` nach `%LocalAppData%\Scrat-Backup\` verschieben

---

## 📋 Systemanforderungen

| | Minimum | Empfohlen |
|---|---|---|
| **Windows** | Windows 10 64-bit | Windows 11 64-bit |
| **Linux** | Ubuntu 22.04 / vergleichbar | Ubuntu 24.04 |
| **RAM** | 4 GB | 8 GB |
| **Speicher** | 500 MB | 1 GB |
| **Python** | nicht nötig (Standalone) | – |

---

## 📖 Weitere Informationen

- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Build-Anleitung:** [BUILD.md](BUILD.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 💬 Support & Community

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions)
- ❓ **Fragen:** [GitHub Discussions Q&A](https://github.com/nicolettas-muggelbude/Scrat-Backup/discussions/categories/q-a)

---

## ⚖️ Lizenz

Scrat-Backup ist **Open Source** unter der **GNU General Public License v3.0**.

Siehe [LICENSE](LICENSE) für Details.

---

<div align="center">

**Wie ein Eichhörnchen seine Eicheln bewahrt, so bewahren wir deine Daten.** 🐿️🌰

[📥 Download](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/tag/v0.3.15-beta) • [⭐ Star auf GitHub](https://github.com/nicolettas-muggelbude/Scrat-Backup) • [🐛 Bug melden](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)

</div>

---

*Erstellt mit ❤️ und [Claude Code](https://claude.com/claude-code)*
