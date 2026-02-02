# TODO vor Release

## Priorität: Hoch

### Wizard V3 - Noch fehlende Features

- [ ] **Restore-Flow im Wizard**
  - Neue Page für Backup-Auswahl
  - Durchsuchen vorhandener Backups
  - Auswahl: Vollständige Wiederherstellung vs. Einzelne Dateien
  - Zielort-Auswahl (Original-Location vs. Eigener Pfad)
  - Integration mit restore_engine.py

- [ ] **System Tray mit Theme-Toggle**
  - Tray-Icon implementieren (läuft im Hintergrund)
  - Kontextmenü: Backup starten, Restore, Einstellungen, Beenden
  - Theme-Toggle im Tray-Menü (Hell/Dunkel/Auto)
  - Benachrichtigungen bei Backup-Start/Ende
  - Autostart-Option (plattformübergreifend)

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

### Internationalisierung (i18n)

- [ ] **Mehrsprachigkeit**
  - Qt Linguist für Übersetzungen
  - QTranslator-Klasse integrieren
  - Sprache automatisch vom OS erkennen
  - Fallback: Englisch wenn Sprache nicht verfügbar
  - Unterstützte Sprachen (Phase 1):
    - 🇩🇪 Deutsch (Primär)
    - 🇬🇧 Englisch
  - Weitere Sprachen (Community-beigetragen):
    - 🇫🇷 Französisch
    - 🇪🇸 Spanisch
    - 🇮🇹 Italienisch
    - 🇳🇱 Niederländisch
    - 🇵🇱 Polnisch
    - 🇷🇺 Russisch

- [ ] **Übersetzungs-Dateien**
  - .ts Dateien für jede Sprache
  - Alle UI-Strings extrahieren
  - Datum/Zeit-Formate lokalisieren
  - Zahlen-Formate lokalisieren (1.000 vs 1,000)
  - Pluralisierung (1 Datei vs 2 Dateien)

- [ ] **Sprachauswahl**
  - Settings → "Sprache"
  - Dropdown mit verfügbaren Sprachen
  - "Automatisch (System)" Option
  - Nach Sprachwechsel: Neustart erforderlich (Info)

- [ ] **Übersetzungs-Workflow**
  - Contributor-Guide für Übersetzer
  - .ts Dateien in Repository
  - GitHub Issues Template für neue Sprachen
  - Weblate/Crowdin für Community-Übersetzungen (optional)

### Dark Mode / Theme-Unterstützung

- [x] **Automatische Dark-Mode-Erkennung** ✅
  - System-Theme-Detection (Windows/Linux/macOS)
  - ThemeManager mit plattformübergreifender Auto-Detection
  - Automatisch umschalten beim OS-Wechsel
  - App-Neustart nicht erforderlich

- [x] **Dark Mode Theme** ✅
  - Dark Theme für alle Widgets
  - Angepasste Farben:
    - Hintergrund: #1e1e1e (dunkelgrau)
    - Text: #e0e0e0 (hellgrau)
    - Akzente: #007acc (blau)
    - Fehler: #f48771 (helles rot)
    - Erfolg: #89d185 (helles grün)
  - Icons für Dark Mode optimieren
  - Kontrast-Verhältnis: ≥ 7:1 (WCAG AAA)

- [ ] **Light Mode Theme**
  - Light Theme (aktuelles Design)
  - Windows 11 Design-Richtlinien
  - Kontrast-Verhältnis: ≥ 4.5:1 (WCAG AA)

- [ ] **Theme-Einstellungen**
  - Settings → "Erscheinungsbild"
  - Theme-Auswahl:
    - "Automatisch (System)"
    - "Hell"
    - "Dunkel"
  - Live-Vorschau beim Wechsel
  - Keine App-Neustart erforderlich

- [ ] **Hochkontrast-Modus**
  - System-Hochkontrast-Einstellungen respektieren (Windows/Linux/macOS)
  - Spezielle Hochkontrast-Farben
  - Barrierefreiheit für sehbehinderte Nutzer

- [ ] **Theme-Engine**
  - Zentrale theme.py erweitern
  - get_theme() → "light" | "dark" | "high_contrast"
  - apply_theme() für dynamisches Umschalten
  - Theme-Change-Event für alle Widgets

### Barrierefreiheit (Accessibility)

- [x] **Tastatur-Navigation** ✅ (Wizard)
  - Alle Wizard-Elemente per Tab-Taste erreichbar
  - Textfeld für direkte Pfad-Eingabe
  - Schnellauswahl-Buttons (Home, Desktop, Dokumente)
  - Focus-Indikatoren sichtbar
  - Workaround für QFileDialog (Qt-Limitation)

- [ ] **Screen-Reader-Unterstützung**
  - Alle Buttons und Felder mit aussagekräftigen Labels
  - Alt-Texte für Icons
  - Status-Ansagen bei langen Operationen ("Backup läuft, 45% abgeschlossen")
  - ARIA-ähnliche Semantik in PyQt6 (wo möglich)

- [x] **Visuelle Barrierefreiheit** ✅ (teilweise)
  - Verbesserter Kontrast (Hover: #e8e8e8, Selection: #d0d0d0)
  - [ ] Hochkontrast-Modus (Windows-Integration) - noch offen
  - [ ] Schriftgröße anpassbar (Strg++ / Strg+-) - noch offen
  - Icons + Text bei allen Buttons (📁, 🏠, 🖥️, 📄)
  - Keine Information nur durch Farbe

- [ ] **Farbenblindheit-freundliche Farbpaletten**
  - **Color Universal Design (CUD)** implementieren
  - Niemals nur Farbe zur Information nutzen:
    - ✅ Erfolg: Grüner Haken + "Erfolgreich" Text
    - ✅ Fehler: Rotes X + "Fehler" Text
    - ✅ Warnung: Gelbes Dreieck + "Achtung" Text
    - ❌ Nur farbige Balken ohne Symbole
  - Rot-Grün-Kombinationen vermeiden
    - Stattdessen: Blau-Orange oder Blau-Gelb
  - Empfohlene Farbpalette (Paul Tol's Bright):
    - Info/Primary: `#4477AA` (Blau)
    - Error: `#EE6677` (Rosa/Rot)
    - Success: `#228833` (Grün)
    - Warning: `#CCBB44` (Gelb)
    - Accent: `#66CCEE` (Cyan)
  - Alternative: IBM Design Colors
    - Blue: `#0F62FE`
    - Magenta: `#EE538B`
    - Teal: `#009D9A`
    - Purple: `#8A3FFC`
  - Alle Status-Meldungen mit Icons + Text + Farbe
  - Fortschrittsbalken mit Muster/Streifen (nicht nur Farbe)

- [ ] **Farbenblindheit testen**
  - Chrome DevTools: "Rendering → Emulate Vision Deficiencies"
    - Protanopia (Rot-Blindheit)
    - Deuteranopia (Grün-Blindheit)
    - Tritanopia (Blau-Blindheit)
    - Achromatopsia (Totale Farbenblindheit)
  - Color Oracle (Desktop-Tool)
  - Coblis Color Blindness Simulator
  - Mit allen 4 Typen testen

- [ ] **Motorische Einschränkungen**
  - Große Klickflächen (mindestens 44×44 Pixel)
  - Großzügige Abstände zwischen interaktiven Elementen
  - Kein doppelter Klick erforderlich
  - Verzögerung vor kritischen Aktionen ("Löschen" mit Bestätigung)

- [ ] **Kognitive Barrierefreiheit**
  - Einfache, klare Sprache
  - Konsistente Navigation
  - Fehlertoleranz (Undo für kritische Aktionen)
  - Fortschrittsanzeigen bei langen Vorgängen

- [ ] **Testen mit Assistiven Technologien**
  - **Windows:** NVDA/Sprachausgabe, Bildschirmlupe
  - **Linux:** Orca Screen-Reader, Compiz Lupe
  - **macOS:** VoiceOver, Zoom
  - Nur-Tastatur-Navigation auf allen Plattformen testen

## Priorität: Mittel

### Update-Funktion

- [ ] **Automatische Update-Prüfung**
  - Beim Start prüfen ob neue Version verfügbar (opt-in)
  - GitHub Releases API abfragen
  - Nur einmal täglich prüfen (Cache mit Zeitstempel)
  - Im Hintergrund, blockiert nicht die GUI

- [ ] **Update-Benachrichtigung**
  - Dezente Benachrichtigung in der Statusbar
  - "Neue Version verfügbar: v1.2.0"
  - Klick öffnet Update-Dialog
  - Changelog anzeigen (aus GitHub Release Notes)
  - "Später erinnern" Button (24h Pause)
  - "Nicht mehr fragen für diese Version" Option

- [ ] **Update-Dialog**
  - Aktuelle Version vs. Neue Version
  - Release-Notes / Changelog formatiert anzeigen
  - Download-Optionen:
    - "Im Browser öffnen" (öffnet GitHub Releases)
    - "Automatisch herunterladen" (optional, Phase 2)
  - "Überspringe diese Version" Checkbox

- [ ] **Automatisches Update** (Phase 2, optional)
  - Installer herunterladen (verifiziert mit Signatur)
  - Backup der aktuellen Installation
  - Silent-Install starten
  - Nach Update: Changelog anzeigen

- [ ] **Update-Einstellungen**
  - Settings → "Updates"
    - [ ] Automatisch nach Updates suchen
    - [ ] Beta-Versionen einbeziehen
    - Update-Kanal: "Stable" / "Beta" / "Aus"
  - "Jetzt nach Updates suchen" Button
  - Letzte Prüfung: Datum/Zeit

- [ ] **Versionsverwaltung**
  - Semantic Versioning (SemVer): v1.2.3
  - version.py mit __version__ = "1.0.0"
  - Im GUI anzeigen (About-Dialog, Statusbar)
  - Build-Nummer für Entwicklungs-Builds

- [ ] **Sicherheit**
  - HTTPS für Update-Prüfung (GitHub API)
  - Signatur-Verifizierung für Downloads
  - Keine Auto-Update ohne User-Bestätigung
  - Privacy: Keine Telemetrie, nur Version-Check

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

## Nach dem Release 🚀

### Marketing & Community

- [ ] **Projektwebseite erstellen**
  - Domain registrieren (z.B. scrat-backup.org)
  - Landingpage mit Features
    - "Schütze deine Daten wie Scrat seine Eicheln! 🐿️"
    - Feature-Highlights mit Icons
    - Screenshots der GUI
    - Download-Buttons (Windows 10/11)
  - Dokumentation online
    - Benutzerhandbuch
    - FAQ
    - Entwickler-Dokumentation
  - Blog/News-Bereich
    - Release-Ankündigungen
    - Tutorials
    - Best Practices
  - GitHub-Integration
    - Link zu Repository
    - Issue-Tracker
    - Roadmap
  - Kontakt/Support
    - E-Mail
    - Discord/Matrix?
    - GitHub Discussions

- [ ] **Social Media Content**
  - **Twitter/X**
    - Release-Ankündigung mit Screenshots
    - Tipps & Tricks (Thread)
    - "Feature Friday" (wöchentlich)
    - Community-Feedback teilen
  - **Reddit**
    - r/selfhosted - "Scrat-Backup: Open-Source Backup für Windows"
    - r/DataHoarder - "Einfache Backup-Lösung"
    - r/opensource - "Neues GPLv3-Projekt"
  - **YouTube**
    - Projektvorstellung (5 Minuten)
    - "Scrat-Backup einrichten" Tutorial
    - Feature-Demos
    - Behind-the-Scenes (Entwicklung)
  - **LinkedIn**
    - Professionelle Projekt-Ankündigung
    - Tech-Blog-Posts
  - **Mastodon**
    - Dezentrale Alternative zu Twitter
    - Tech-Community sehr aktiv

- [ ] **Open-Source-Verzeichnisse**
  - AlternativeTo.net
  - SourceForge (Mirror)
  - Softpedia
  - GitHub Awesome-Lists (z.B. awesome-selfhosted)
  - FossHub

- [ ] **Pressearbeit**
  - **Pressemitteilung schreiben**
    - "Scrat-Backup: Neue Open-Source-Backup-Lösung für Windows"
    - Feature-Liste
    - Download-Links
  - **Tech-Blogs kontaktieren**
    - Heise.de (deutschsprachig)
    - Golem.de
    - t3n.de
    - Netzpolitik.org (Open-Source-Fokus)
  - **Internationale Medien**
    - It's FOSS
    - OMG! Ubuntu (auch für Windows relevant)
    - ghacks.net

- [ ] **Community aufbauen**
  - GitHub Discussions aktivieren
  - Discord/Matrix-Server (optional)
  - Contributor-Guide schreiben
  - "Good First Issue" Labels für Einsteiger
  - Code of Conduct
  - Contribution Guidelines

- [ ] **Produkthunt Launch** (optional)
  - Produkthunt-Eintrag vorbereiten
  - Screenshots, GIFs, Video
  - "Hunter" finden (jemand mit vielen Followern)
  - Launch-Tag planen (Dienstag-Donnerstag am besten)

### Analytics & Feedback

- [ ] **Nutzungsstatistiken (opt-in, anonym)**
  - Beliebte Features tracken
  - Fehler-Reporting (Sentry?)
  - Download-Zahlen

- [ ] **Feedback-Kanäle**
  - In-App Feedback-Button
  - User-Umfragen
  - Feature-Requests (GitHub Issues)

### Sponsoring & Spenden

- [ ] **Sponsoring-Plattformen einrichten**
  - **GitHub Sponsors** (Primär)
    - Direkt auf GitHub-Repo-Seite sichtbar
    - Monatliche/einmalige Spenden
    - Sponsor-Button im Repo
  - **Open Collective** (Alternativ)
    - Transparente Finanzen
    - Community-verwaltet
    - Ausgaben öffentlich sichtbar
  - **Ko-fi** (Für einmalige Spenden)
    - Einfach & schnell
    - "Buy me a coffee" Stil
  - **Liberapay** (Europa-freundlich)
    - SEPA-freundlich
    - Wöchentliche Unterstützung

- [ ] **FUNDING.yml erstellen**
  - .github/FUNDING.yml Datei
  - Sponsoring-Button auf GitHub
  - Links zu allen Plattformen

- [ ] **Sponsor-Tiers definieren**
  - 🥉 **Bronze** ($5/Monat)
    - Name in SPONSORS.md
    - Dankeschön-E-Mail
  - 🥈 **Silver** ($25/Monat)
    - Name + Logo in README.md
    - Name auf Projektwebseite
  - 🥇 **Gold** ($100/Monat)
    - Prominentes Logo in README + Website
    - Erwähnung in Release-Notes
    - Prioritäts-Support
  - 💎 **Platinum** ($500/Monat)
    - Alle Gold-Vorteile
    - Einfluss auf Roadmap
    - Private Consulting (1h/Monat)

- [ ] **SPONSORS.md erstellen**
  - Liste aller aktuellen Sponsoren
  - Danksagungen
  - Verwendung der Mittel transparent darstellen

- [ ] **Sponsoring-Seite auf Website**
  - "Unterstütze Scrat-Backup"
  - Vorteile für Sponsoren
  - Verwendung der Spenden:
    - Entwicklungszeit
    - Hosting-Kosten
    - Domain-Kosten
    - Marketing
  - Finanz-Transparenz (monatlicher Report)

- [ ] **Sponsor-Logo-Integration**
  - Automatisches Logo-Update in README
  - GitHub Action für Sponsor-Sync
  - Sponsor-Slider auf Website

- [ ] **Dankeschön-System**
  - Automatische E-Mail an neue Sponsoren
  - Monatlicher Newsletter für Sponsoren
  - Erwähnung in Release-Notes
  - Social Media Shout-Outs

- [ ] **Verwendung transparent kommunizieren**
  - Monatlicher Finanz-Report
  - Ausgaben aufschlüsseln:
    - Entwicklung: X Stunden á Y €
    - Infrastruktur: Server, Domain
    - Marketing: Anzeigen, etc.
  - Open Collective für volle Transparenz

- [ ] **Steuerliche Aspekte klären**
  - Freiberuflich vs. Gewerbe
  - Umsatzsteuer (Kleinunternehmer?)
  - Spendenquittungen (wenn gemeinnützig)
  - Steuererklärung

## Abgeschlossen ✅

- [x] Setup-Wizard komplett überarbeitet (2025-12-02)
  - Alle Buttons auf Deutsch
  - Icon und Version
  - Persönliche Ordner ohne Pfade
  - Automatische Laufwerk-Erkennung
  - WebDAV, Rclone, SMB/CIFS Optionen
  - Passwort-Bug gefixt
  - Bessere Darstellung von "Alte Backups behalten"

- [x] Template-System & Wizard V2 (2026-02-01)
  - TemplateManager mit 7 Templates (USB, OneDrive, Google Drive, Nextcloud, Dropbox, Synology, QNAP)
  - DynamicTemplateForm mit Handler-Actions
  - Template-basierte Konfiguration funktionsfähig

- [x] Wizard V3 - Barrierefreiheit & UX (2026-02-02)
  - Dark Mode mit automatischer System-Erkennung (Windows/Linux/macOS)
  - Einheitliches Design (StartPage & ModePage ohne Frames)
  - Tastatur-Navigation in Wizard implementiert
  - Textfeld + Schnellauswahl für Ordner-Eingabe
  - Plattformspezifische Features (Ausschlüsse, Bibliotheken)
  - Besserer Kontrast (Hover & Selection)
  - Deutsche Qt-Übersetzungen geladen
  - Icons bei allen Ordner-Einträgen (📁)
  - **Cross-Platform:** Funktioniert identisch auf Windows, Linux, macOS
  - **Einschränkung:** QFileDialog selbst nicht vollständig tastatur-bedienbar (Qt-Limitation)

- [x] Wizard V3 - Weitere Verbesserungen (2026-02-02)
  - Version-Integration über Parameter-Übergabe (run_wizard.py → wizard_v2.py)
  - Akzentfarbe globalisiert (get_color("primary") aus theme.py)
  - sourcesChanged Signal für reaktiven Weiter-Button
  - DynamicTemplateForm erweitert:
    - drive_selector Feldtyp (USB-Laufwerk-Auswahl mit Refresh)
    - checkbox Feldtyp implementiert
  - **USB-Template vollständig funktionsfähig! 💾**

---

**Letzte Aktualisierung:** 2026-02-02
**Version:** 0.2.0-dev
**Status:** Pre-Release (Wizard V3 produktionsreif, USB-Template funktioniert)
