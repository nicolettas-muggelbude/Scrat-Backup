# 🎉 Scrat-Backup v0.3.14-beta Release Notes

## 💾 Downloads

| Plattform | Download |
|-----------|----------|
| 🪟 **Windows** (x64) | [⬇ ScratBackup-v0.3.14-beta-Setup.exe](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.14-beta/ScratBackup-v0.3.14-beta-Setup.exe) |
| 🐧 **Linux** (x86_64, versioniert) | [⬇ ScratBackup-v0.3.14-beta-x86_64.AppImage](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.14-beta/ScratBackup-v0.3.14-beta-x86_64.AppImage) |
| 🐧 **Linux** (x86_64, neutral) | [⬇ ScratBackup-x86_64.AppImage](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.14-beta/ScratBackup-x86_64.AppImage) |
| 🐧 **Linux** Desktop-Integration | [⬇ install.sh](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/download/v0.3.14-beta/install.sh) |

---

## 🐿️ Update-Benachrichtigung + USB-Backup + neutrales AppImage

**Scrat-Backup v0.3.14-beta** behebt drei Bugs: Die Update-Benachrichtigung erscheint jetzt während der Wizard offen ist, USB-Backup übergibt Laufwerk und Pfad korrekt, und es gibt ein versionsloses AppImage für stabile Download-Links.

---

## 🔧 Bugfixes

### USB-Backup: Laufwerksauswahl wurde ignoriert
Das Formular auf der Ziel-Seite zeigte Felder an, speicherte aber keine Werte – weil alle ui_fields übersprungen wurden. Der Code suchte nach dem Schlüssel `"name"`, die Template-JSONs verwenden aber `"id"`. Dadurch wurde kein Laufwerk, kein Unterordner übergeben.

### Handler-Laden schlug lautlos fehl
Der Ladepfad für Template-Handler wurde falsch zusammengebaut:  
`templates.handlers.src.templates.handlers.usb_handler.UsbHandler` statt dem richtigen Modul.  
Ohne Handler kein Formular, ohne Formular kein Ziel, ohne Ziel kein Backup.

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
- ✅ **TemplateDestinationPage** – Template-Kacheln, nicht verfügbare Backends gesperrt
- ✅ **SchedulePage** – Täglich/Wöchentlich/Monatlich/beim Start, Zeitangabe, Wochentag
- ✅ **EncryptionPage** – Passwort + Keyring
- ✅ **RestoreWizardPage** – DB- und Verzeichnis-Modus
- ✅ **FinishPage** – Tray-Start oder Experten-Modus

### Dark Mode
- ✅ Auto-Detection + manuelles Umschalten
- ✅ Alle Wizard-Seiten theme-aware (TemplateCards, Ordner-Liste, Ausschlüsse, FinishPage)

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

[📥 Download](https://github.com/nicolettas-muggelbude/Scrat-Backup/releases/tag/v0.3.14-beta) • [⭐ Star auf GitHub](https://github.com/nicolettas-muggelbude/Scrat-Backup) • [🐛 Bug melden](https://github.com/nicolettas-muggelbude/Scrat-Backup/issues)

</div>

---

*Erstellt mit ❤️ und [Claude Code](https://claude.com/claude-code)*
