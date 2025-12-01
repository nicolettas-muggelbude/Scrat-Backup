# TODO vor Release

## Priorität: Hoch

### Hilfefunktion / Guided Tour
- [ ] **Setup-Wizard: Hilfe-Button auf jeder Seite**
  - Kontextbezogene Hilfe für jede Wizard-Seite
  - Erklärt was der Benutzer eingeben muss
  - Beispiele für typische Konfigurationen

- [ ] **Erste-Schritte-Tutorial**
  - Nach dem ersten Start: "Willkommen bei Scrat-Backup" Dialog
  - Schritt-für-Schritt Anleitung für erstes Backup
  - Optional überspringbar ("Nicht mehr anzeigen")

- [ ] **Tooltips im Hauptfenster**
  - Alle Buttons mit Tooltips versehen
  - Erklärung der verschiedenen Backup-Typen (Voll vs. Inkrementell)
  - Info-Icons (ⓘ) bei komplexeren Optionen

- [ ] **Hilfe-Menü**
  - "Hilfe" → "Erste Schritte"
  - "Hilfe" → "Häufige Fragen (FAQ)"
  - "Hilfe" → "Über Scrat-Backup"

- [ ] **In-App Dokumentation**
  - FAQ-Seite im GUI integrieren
  - Troubleshooting-Guide
  - Best Practices für Backups

### Benutzerfreundlichkeit

- [ ] **Validierung verbessern**
  - Echtzeit-Validierung in Eingabefeldern
  - Grüne Häkchen bei gültigen Eingaben
  - Rote Warnungen bei Problemen

- [ ] **Rückmeldungen verbessern**
  - "Backup erfolgreich" mit Details (Größe, Dauer, Dateien)
  - "Passwort gespeichert" Bestätigung
  - Fortschrittsanzeige für lange Operationen

- [ ] **Fehlermeldungen benutzerfreundlicher**
  - Technische Fehler in einfache Sprache übersetzen
  - Lösungsvorschläge anbieten
  - "Weitere Hilfe" Button → öffnet FAQ

## Priorität: Mittel

### Stabilität & Tests

- [ ] **Vollständige Test-Coverage**
  - GUI-Tests für alle Tabs
  - Integration-Tests für Storage-Backends
  - End-to-End-Tests für komplette Backup/Restore-Zyklen

- [ ] **Error-Handling**
  - Graceful Degradation bei Netzwerkfehlern
  - Wiederholungsmechanismus für fehlgeschlagene Uploads
  - Cleanup bei abgebrochenen Backups

### Performance

- [ ] **Große Dateien optimieren**
  - Streaming für Dateien > 1GB
  - Chunk-Upload für bessere Fortschrittsanzeige
  - Memory-Management bei vielen kleinen Dateien

### Dokumentation

- [ ] **Benutzerhandbuch schreiben**
  - Installation unter Windows
  - Erste Schritte
  - Erweiterte Konfiguration
  - Troubleshooting

- [ ] **Video-Tutorials (optional)**
  - YouTube: "Scrat-Backup in 5 Minuten"
  - Backup erstellen
  - Dateien wiederherstellen

## Priorität: Niedrig

### Nice-to-Have

- [ ] **Backup-Statistiken**
  - Dashboard mit Backup-Historie
  - Grafische Darstellung der Backup-Größen
  - Speicherplatz-Trends

- [ ] **Backup-Verifizierung**
  - Automatische Prüfung nach Backup
  - Hash-Vergleich
  - "Backup testen" Funktion

- [ ] **Cloud-Provider Quick-Setup**
  - Vorkonfigurierte Templates für beliebte Cloud-Provider
  - "Google Drive", "Dropbox", "OneDrive" Buttons
  - Automatische rclone-Konfiguration (wenn möglich)

## Abgeschlossen ✅

- [x] Setup-Wizard komplett überarbeitet (2025-12-02)
  - Alle Buttons auf Deutsch
  - Icon und Version
  - Persönliche Ordner ohne Pfade
  - Automatische Laufwerk-Erkennung
  - WebDAV, Rclone, SMB/CIFS Optionen
  - Passwort-Bug gefixt
  - Bessere Darstellung von "Alte Backups behalten"

---

**Letzte Aktualisierung:** 2025-12-02
**Version:** 0.1.0-dev
