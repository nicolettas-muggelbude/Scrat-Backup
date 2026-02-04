"""
Wizard Pages - Neugestaltete Wizard-Seiten
Barrierefreundlich mit Radio-Buttons
"""

import logging
import platform
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QWizardPage,
)

from core.config_manager import ConfigManager
from gui.theme import get_color

logger = logging.getLogger(__name__)


class ClickableFrame(QFrame):
    """QFrame das Clicks an das parent QListWidget weitergibt"""

    def __init__(self, list_widget: QListWidget, item: QListWidgetItem, parent=None):
        super().__init__(parent)
        self.list_widget = list_widget
        self.item = item

    def mousePressEvent(self, event):
        """Bei Click: Selektiere das zugehörige Item"""
        super().mousePressEvent(event)
        self.list_widget.setCurrentItem(self.item)


class StartPage(QWizardPage):
    """
    Neue erste Wizard-Seite

    Unterscheidet zwischen:
    - Ersteinrichtung (keine Config)
    - Bestehendes System (Config vorhanden)

    Features:
    - Radio-Buttons (Barrierefreiheit)
    - Config-Check
    - Backup vs. Restore Auswahl
    """

    # Signals
    action_selected = Signal(str)  # "backup", "restore", "edit", "expert"

    def __init__(self, parent=None):
        super().__init__(parent)

        # Prüfe ob Config existiert
        self.has_config = self._check_config_exists()

        # Setup UI
        self.setTitle("Willkommen bei Scrat-Backup! 🐿️")

        if self.has_config:
            self.setSubTitle("Dein Backup-System ist bereits eingerichtet. " "Was möchtest du tun?")
        else:
            self.setSubTitle("Richte dein Backup-System ein oder stelle Dateien wieder her.")

        # Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Info-Text
        if not self.has_config:
            info = QLabel(
                "👋 Dies ist deine erste Verwendung von Scrat-Backup.\n"
                "Wähle eine der folgenden Optionen:"
            )
        else:
            info = QLabel("Was möchtest du tun?")

        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(info)

        # Button-Group für Radio-Buttons
        self.button_group = QButtonGroup(self)
        self.selected_action = None
        self.radio_buttons = {}  # Speichert Radio-Buttons für späteren Zugriff

        # Erstelle Optionen basierend auf Config-Status
        if self.has_config:
            self._create_existing_system_options(layout)
        else:
            self._create_first_run_options(layout)

        layout.addStretch()

        # Registriere Feld für Wizard
        self.registerField("start_action*", self, "selectedAction")

    def _check_config_exists(self) -> bool:
        """
        Prüft ob gültige Config existiert

        Returns:
            True wenn Config vorhanden und gültig
        """
        config_dir = Path.home() / ".scrat-backup"
        config_file = config_dir / "config.json"

        if not config_file.exists():
            return False

        try:
            config_manager = ConfigManager(config_file)

            has_sources = (
                config_manager.config.get("sources") and len(config_manager.config["sources"]) > 0
            )
            has_destinations = (
                config_manager.config.get("destinations")
                and len(config_manager.config["destinations"]) > 0
            )

            return has_sources and has_destinations

        except Exception as e:
            logger.warning(f"Fehler beim Laden der Config: {e}")
            return False

    def _create_first_run_options(self, layout: QVBoxLayout):
        """Erstellt Optionen für Ersteinrichtung"""

        # Option 1: Backup einrichten
        backup_frame = self._create_option_radio(
            "backup", "📦 Backup einrichten", "Sichere deine wichtigen Dateien regelmäßig"
        )
        layout.addWidget(backup_frame)

        # Spacing (wie ModePage)
        layout.addSpacing(15)

        # Option 2: Backup wiederherstellen
        restore_frame = self._create_option_radio(
            "restore",
            "♻️ Backup wiederherstellen (Restore)",
            "Stelle Dateien aus einem vorhandenen Backup wieder her",
        )
        layout.addWidget(restore_frame)

        # Standard-Auswahl (über gespeicherten Radio-Button)
        if "backup" in self.radio_buttons:
            self.radio_buttons["backup"].setChecked(True)
            self.selected_action = "backup"

    def _create_existing_system_options(self, layout: QVBoxLayout):
        """Erstellt Optionen für bestehendes System"""

        # Option 1: Einstellungen ändern
        edit_frame = self._create_option_radio(
            "edit", "⚙️ Backup-Einstellungen ändern", "Ändere Quellen, Ziele oder Zeitplan"
        )
        layout.addWidget(edit_frame)

        # Spacing (wie ModePage)
        layout.addSpacing(15)

        # Option 2: Neues Ziel hinzufügen
        add_frame = self._create_option_radio(
            "add_destination",
            "➕ Neues Backup-Ziel hinzufügen",
            "Füge ein weiteres Backup-Ziel hinzu",
        )
        layout.addWidget(add_frame)

        # Spacing (wie ModePage)
        layout.addSpacing(15)

        # Option 3: Restore
        restore_frame = self._create_option_radio(
            "restore",
            "♻️ Backup wiederherstellen (Restore)",
            "Stelle Dateien aus einem deiner Backups wieder her",
        )
        layout.addWidget(restore_frame)

        # Spacing (wie ModePage)
        layout.addSpacing(15)

        # Option 4: Experten-Modus
        expert_frame = self._create_option_radio(
            "expert", "🔧 Experten-Modus", "Vollständige Kontrolle über alle Einstellungen"
        )
        layout.addWidget(expert_frame)

        # Standard-Auswahl (über gespeicherten Radio-Button)
        if "edit" in self.radio_buttons:
            self.radio_buttons["edit"].setChecked(True)
            self.selected_action = "edit"

    def _create_option_radio(self, action_id: str, title: str, description: str) -> QWidget:
        """
        Erstellt eine Option als Radio-Button mit Beschreibung
        (Style wie ModePage - ohne Frame/Border)

        Args:
            action_id: ID der Aktion
            title: Titel der Option
            description: Beschreibung

        Returns:
            QWidget mit Radio-Button und Beschreibung
        """
        # Container ohne Styling
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Radio-Button mit Titel (wie ModePage)
        radio = QRadioButton(title)
        radio.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.button_group.addButton(radio)

        # Speichere Action-ID
        radio.setProperty("action_id", action_id)

        # Speichere Radio-Button für späteren Zugriff
        self.radio_buttons[action_id] = radio

        # Bei Klick: Action setzen
        radio.toggled.connect(lambda checked: self._on_radio_toggled(radio, checked))

        layout.addWidget(radio)

        # Beschreibung (eingerückt, wie ModePage)
        desc_label = QLabel(f"    {description}")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 13px; margin-left: 30px;")
        layout.addWidget(desc_label)

        return container

    def _create_separator(self) -> QFrame:
        """Erstellt horizontale Trennlinie"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #e0e0e0;")
        return line

    def _on_radio_toggled(self, radio: QRadioButton, checked: bool):
        """Wird aufgerufen wenn Radio-Button geändert wird"""
        if checked:
            action_id = radio.property("action_id")
            self.selected_action = action_id
            logger.info(f"Aktion gewählt: {action_id}")

            # Signal aussenden
            self.action_selected.emit(action_id)

            # Trigger completeChanged für Wizard
            self.completeChanged.emit()

    # Property für Wizard-Feld
    @property
    def selectedAction(self) -> str:
        """Gibt gewählte Aktion zurück"""
        return self.selected_action or ""

    def isComplete(self) -> bool:
        """Prüft ob Seite vollständig ist (für Weiter-Button)"""
        return self.selected_action is not None and self.selected_action != ""

    def validatePage(self) -> bool:
        """Validiert Seite vor Weiter"""
        if not self.selected_action:
            return False

        # Bei Experten-Modus: MainWindow öffnen
        if self.selected_action == "expert":
            logger.info("Experten-Modus gewählt - MainWindow wird geöffnet")
            # TODO: MainWindow öffnen
            return False  # Wizard nicht weitergehen

        return True

    def nextId(self) -> int:
        """
        Bestimmt nächste Seite basierend auf Auswahl

        Returns:
            ID der nächsten Seite
        """
        # Page-IDs (korrespondieren zu wizard_v2.py)
        PAGE_MODE = 2
        PAGE_DESTINATION = 3
        PAGE_FINISH = 5

        if self.selected_action == "backup":
            # Backup einrichten → Erst Modus wählen (Normal/Experten)
            return PAGE_MODE

        elif self.selected_action == "restore":
            # Restore → Vorerst zum Finish mit Hinweis
            # TODO: Eigener Restore-Flow
            return PAGE_FINISH

        elif self.selected_action in ["edit", "add_destination"]:
            # TODO: "edit" sollte auch PAGE_SOURCE durchlaufen, damit Quellen
            # geändert werden können. Aktuell wird nur das Ziel angezeigt.
            # Direkt zu Destination
            return PAGE_DESTINATION

        elif self.selected_action == "expert":
            # Experten-Modus → Wizard beendet sich in validatePage()
            return -1

        # Fallback
        return super().nextId()


# ============================================================================
# SOURCE SELECTION PAGE - Was sichern?
# ============================================================================


class SourceSelectionPage(QWizardPage):
    """
    Quell-Auswahl - Was soll gesichert werden?

    Features:
    - Standard-Bibliotheken (Dokumente, Bilder, Videos, Desktop, Musik)
    - Eigene Ordner hinzufügen
    - Standard-Ausschlüsse (*.tmp, *.cache, etc.)
    - Übersicht der gewählten Quellen
    """

    # Signal wenn sich Quellen ändern
    sourcesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTitle("Was möchtest du sichern?")
        self.setSubTitle(
            "Wähle die Ordner und Bibliotheken aus, die regelmäßig gesichert werden sollen."
        )

        # Daten
        self.standard_libraries = self._get_standard_libraries()
        self.library_checkboxes: dict[str, QCheckBox] = {}
        self.custom_sources: List[str] = []
        self.exclude_patterns = self._get_default_excludes()

        # UI erstellen
        self._init_ui()

        # Versteckte QLineEdits als Feld-Träger
        # (PySide6 kann @property nicht über Qt-Property lesen)
        self._sources_edit = QLineEdit(self)
        self._sources_edit.setVisible(False)
        self._excludes_edit = QLineEdit(self)
        self._excludes_edit.setVisible(False)
        self._excludes_edit.setText(self.excludePatterns)  # Excludes sind statisch

        # Registriere Felder auf den versteckten QLineEdits
        self.registerField("sources*", self._sources_edit)
        self.registerField("excludes", self._excludes_edit)

    def _init_ui(self):
        """Initialisiert UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Scroll-Area für Inhalt
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)

        # 1. Standard-Bibliotheken
        libraries_group = self._create_libraries_group()
        scroll_layout.addWidget(libraries_group)

        # 2. Eigene Ordner
        custom_group = self._create_custom_group()
        scroll_layout.addWidget(custom_group)

        # 3. Ausschlüsse (Info)
        excludes_group = self._create_excludes_group()
        scroll_layout.addWidget(excludes_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    def _get_standard_libraries(self) -> dict[str, Path]:
        """
        Ermittelt Standard-Bibliotheken (plattformabhängig)

        Returns:
            Dictionary {name: path}
        """
        system = platform.system()
        libraries = {}

        if system == "Windows":
            # Windows: User-Ordner
            user_home = Path.home()

            # Standard-Bibliotheken
            potential_libs = {
                "Dokumente": user_home / "Documents",
                "Bilder": user_home / "Pictures",
                "Videos": user_home / "Videos",
                "Musik": user_home / "Music",
                "Desktop": user_home / "Desktop",
                "Downloads": user_home / "Downloads",
            }

        elif system == "Linux":
            user_home = Path.home()

            # XDG User Directories
            potential_libs = {
                "Dokumente": user_home / "Documents",
                "Bilder": user_home / "Pictures",
                "Videos": user_home / "Videos",
                "Musik": user_home / "Music",
                "Desktop": user_home / "Desktop",
                "Downloads": user_home / "Downloads",
            }

        elif system == "Darwin":  # macOS
            user_home = Path.home()

            potential_libs = {
                "Dokumente": user_home / "Documents",
                "Bilder": user_home / "Pictures",
                "Videos": user_home / "Movies",
                "Musik": user_home / "Music",
                "Desktop": user_home / "Desktop",
                "Downloads": user_home / "Downloads",
            }

        else:
            logger.warning(f"Unbekanntes System: {system}")
            return {}

        # Nur existierende Ordner zurückgeben
        for name, path in potential_libs.items():
            if path.exists():
                libraries[name] = path
            else:
                logger.debug(f"Bibliothek '{name}' nicht gefunden: {path}")

        return libraries

    def _get_default_excludes(self) -> List[str]:
        """
        Standard-Ausschluss-Muster (plattformabhängig)

        Returns:
            Liste von Glob-Patterns
        """
        system = platform.system()

        # Plattformunabhängige Patterns
        excludes = [
            # Temporäre Dateien
            "*.tmp",
            "*.temp",
            "*.cache",
            "*.log",
            "*.bak",
            "*~",
            # Editor-Dateien
            "*.swp",  # Vim swap files
            "*.swo",
            ".*.sw?",
            # Versionskontrolle
            ".git/",
            ".svn/",
            ".hg/",
            # Build & Dependencies
            "node_modules/",
            "__pycache__/",
            "*.pyc",
            ".venv/",
            "venv/",
            # IDE
            ".vscode/",
            ".idea/",
            "*.sublime-workspace",
        ]

        # Windows-spezifisch
        if system == "Windows":
            excludes.extend(
                [
                    # System
                    "Thumbs.db",
                    "desktop.ini",
                    "~$*",  # Office temporäre Dateien
                    "$RECYCLE.BIN/",
                    # Cache & Temp
                    "AppData/Local/Temp/",
                    "AppData/Local/Microsoft/Windows/Explorer/",  # Thumbnails
                    "AppData/Local/Microsoft/Windows/INetCache/",  # IE Cache
                    "AppData/Local/*/Cache/",  # App-Caches
                    "AppData/Local/*/cache/",
                    "AppData/Local/*/cache2/",
                    # Browser-Cache
                    "AppData/Local/Google/Chrome/*/Cache/",
                    "AppData/Local/Microsoft/Edge/*/Cache/",
                    "AppData/Local/Mozilla/Firefox/*/cache2/",
                ]
            )

        # Linux-spezifisch
        elif system == "Linux":
            excludes.extend(
                [
                    # Papierkorb
                    ".Trash-*/",
                    ".local/share/Trash/",
                    # Cache
                    ".cache/",
                    ".thumbnails/",
                    # Browser-Cache
                    ".mozilla/firefox/*/Cache/",
                    ".mozilla/firefox/*/cache2/",
                    ".config/google-chrome/*/Cache/",
                    ".config/chromium/*/Cache/",
                    # App-spezifische Caches
                    ".config/*/cache/",
                    ".local/share/*/cache/",
                    # Sonstiges
                    "*.~lock.*",  # LibreOffice
                    ".directory",  # KDE
                    ".~*",  # Backup-Dateien
                ]
            )

        # macOS-spezifisch
        elif system == "Darwin":
            excludes.extend(
                [
                    # System
                    ".DS_Store",
                    ".AppleDouble/",
                    ".LSOverride",
                    ".Spotlight-V100/",
                    ".Trashes",
                    # Cache
                    "Library/Caches/",
                    ".cache/",
                    # Browser-Cache
                    "Library/Application Support/Google/Chrome/*/Cache/",
                    "Library/Application Support/Firefox/*/cache2/",
                    "Library/Safari/LocalStorage/",
                    # App-spezifische Caches
                    "Library/Application Support/*/cache/",
                    "Library/Application Support/*/Cache/",
                ]
            )

        return excludes

    def _create_libraries_group(self) -> QGroupBox:
        """Erstellt Standard-Bibliotheken-Gruppe mit Schnellauswahl"""
        group = QGroupBox("📚 Standard-Bibliotheken & Schnellauswahl")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")

        layout = QVBoxLayout(group)

        # Schnellauswahl-Buttons OBEN
        quick_layout = QHBoxLayout()
        quick_label = QLabel("Schnellauswahl:")
        quick_label.setStyleSheet("color: #666; font-size: 11px; font-weight: normal;")
        quick_layout.addWidget(quick_label)

        # Buttons für häufige Ordner
        quick_folders = {
            "🏠 Home": str(Path.home()),
            "🖥️ Desktop": str(Path.home() / "Desktop"),
            "📄 Dokumente": str(Path.home() / "Documents"),
        }

        self.quick_buttons = {}  # Speichere Buttons für später
        for label, path in quick_folders.items():
            if Path(path).exists():
                btn = QPushButton(label)
                btn.setStyleSheet("font-size: 11px; padding: 4px 8px;")
                btn.setCheckable(True)  # Toggle-Button
                btn.clicked.connect(
                    lambda checked, p=path, lbl=label: (
                        self._on_quick_folder_clicked(p, lbl, checked)
                    )
                )
                quick_layout.addWidget(btn)
                self.quick_buttons[label] = btn

        quick_layout.addStretch()
        layout.addLayout(quick_layout)

        layout.addSpacing(10)

        if not self.standard_libraries:
            no_libs = QLabel("⚠️ Keine Standard-Bibliotheken gefunden")
            no_libs.setStyleSheet("color: #666;")
            layout.addWidget(no_libs)
        else:
            # Info
            info = QLabel("Oder wähle einzelne Ordner aus:")
            info.setWordWrap(True)
            info.setStyleSheet("color: #666; font-size: 12px; font-weight: normal;")
            layout.addWidget(info)

            # Checkboxen für jede Bibliothek
            for name, path in self.standard_libraries.items():
                # Checkbox mit Icon und Namen
                checkbox = QCheckBox(f"📁 {name}")
                checkbox.setToolTip(str(path))
                checkbox.setStyleSheet("font-size: 13px;")

                # Sublabel mit Pfad (grau, klein)
                path_label = QLabel(f"    {path}")
                path_label.setStyleSheet("margin-left: 25px; color: #666; font-size: 11px;")

                # Standard: Dokumente, Bilder, Videos ausgewählt
                if name in ["Dokumente", "Bilder", "Videos"]:
                    checkbox.setChecked(True)

                # Bei Änderung: Update & Home-Button Check
                checkbox.stateChanged.connect(self._on_library_changed)

                self.library_checkboxes[name] = checkbox
                layout.addWidget(checkbox)
                layout.addWidget(path_label)

        return group

    def _create_custom_group(self) -> QGroupBox:
        """Erstellt Gruppe für eigene Ordner"""
        group = QGroupBox("📂 Eigene Ordner")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")

        layout = QVBoxLayout(group)

        # Info
        info = QLabel(
            "Füge weitere Ordner hinzu, die nicht in den Standard-Bibliotheken enthalten sind:"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 12px; font-weight: normal;")
        layout.addWidget(info)

        # Pfad-Eingabe + Durchsuchen-Button (horizontal)
        path_layout = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Pfad zum Ordner eingeben oder durchsuchen...")
        self.path_input.returnPressed.connect(self._add_path_from_input)
        path_layout.addWidget(self.path_input, stretch=3)

        browse_btn = QPushButton("📁 Durchsuchen")
        browse_btn.clicked.connect(self._browse_folder)
        path_layout.addWidget(browse_btn, stretch=1)

        add_btn = QPushButton("➕ Hinzufügen")
        add_btn.clicked.connect(self._add_path_from_input)
        add_btn.setDefault(True)
        path_layout.addWidget(add_btn, stretch=1)

        layout.addLayout(path_layout)

        layout.addSpacing(10)

        # Liste der benutzerdefinierten Ordner
        self.custom_list = QListWidget()
        self.custom_list.setMaximumHeight(150)
        self.custom_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                border: none;
                background: transparent;
            }
            QListWidget::item:hover {
                background: transparent;
            }
            QListWidget::item:selected {
                background: transparent;
                border: none;
            }
            QListWidget::item:focus {
                outline: none;
                border: none;
            }
        """)
        self.custom_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.custom_list)

        # Dictionary zum Speichern der Widgets für Selection-Handling
        self.custom_widgets = {}  # {path: (item, widget)}

        # Remove-Button
        remove_btn = QPushButton("➖ Ausgewählten Ordner entfernen")
        remove_btn.clicked.connect(self._remove_custom_folder)
        layout.addWidget(remove_btn)

        return group

    def _create_excludes_group(self) -> QGroupBox:
        """Erstellt Ausschlüsse-Info-Gruppe"""
        group = QGroupBox("🚫 Ausschlüsse")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")

        layout = QVBoxLayout(group)

        # Info
        info = QLabel("Die folgenden Dateitypen werden automatisch vom Backup ausgeschlossen:")
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 12px; font-weight: normal;")
        layout.addWidget(info)

        # Ausschlüsse anzeigen
        excludes_text = ", ".join(self.exclude_patterns[:8])
        if len(self.exclude_patterns) > 8:
            excludes_text += f" ... (+{len(self.exclude_patterns) - 8} weitere)"

        excludes_label = QLabel(excludes_text)
        excludes_label.setWordWrap(True)
        excludes_label.setStyleSheet(
            "color: #999; font-size: 11px; font-weight: normal; "
            "background-color: #f5f5f5; padding: 8px; border-radius: 4px;"
        )
        layout.addWidget(excludes_label)

        # Hinweis
        hint = QLabel("💡 Tipp: Temporäre Dateien, Caches und System-Dateien werden übersprungen.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 11px; font-weight: normal;")
        layout.addWidget(hint)

        return group

    def _browse_folder(self):
        """Öffnet Datei-Dialog zum Durchsuchen (für Maus-Nutzer)"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Ordner zum Sichern auswählen",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog,
        )

        if folder:
            self.path_input.setText(folder)
            self._add_path_from_input()

    def _add_path_from_input(self):
        """Fügt Pfad aus Textfeld hinzu (für Tastatur-Nutzer)"""
        path_text = self.path_input.text().strip()
        if not path_text:
            return

        folder_path = Path(path_text).expanduser().resolve()

        if not folder_path.exists():
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self, "Ordner nicht gefunden", f"Der Ordner existiert nicht:\n{folder_path}"
            )
            return

        if not folder_path.is_dir():
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Kein Ordner", f"Der Pfad ist kein Ordner:\n{folder_path}")
            return

        self._add_folder_to_list(folder_path)
        self.path_input.clear()

    def _on_quick_folder_clicked(self, path: str, label: str, checked: bool):
        """Wird aufgerufen wenn ein Schnellauswahl-Button geklickt wird"""
        folder_path = Path(path)

        if checked:
            # Button wurde aktiviert - Ordner hinzufügen
            self._add_folder_to_list(folder_path)

            # Wenn "Home" ausgewählt wurde: Bibliotheken deaktivieren
            if "Home" in label:
                for checkbox in self.library_checkboxes.values():
                    checkbox.setEnabled(False)
                    checkbox.setChecked(False)
                    checkbox.setStyleSheet("font-size: 13px; color: #999;")

                # Desktop & Dokumente-Buttons deaktivieren (redundant)
                for btn_label, btn in self.quick_buttons.items():
                    if btn_label != label:  # Nicht den Home-Button selbst
                        btn.setEnabled(False)
        else:
            # Button wurde deaktiviert - Ordner entfernen
            if str(folder_path) in self.custom_sources:
                self.custom_sources.remove(str(folder_path))

                # Entferne aus Liste-Widget wenn vorhanden
                if str(folder_path) in self.custom_widgets:
                    item, widget = self.custom_widgets[str(folder_path)]
                    row = self.custom_list.row(item)
                    self.custom_list.takeItem(row)
                    del self.custom_widgets[str(folder_path)]

            # Wenn "Home" deaktiviert wurde: Bibliotheken wieder aktivieren
            if "Home" in label:
                for checkbox in self.library_checkboxes.values():
                    checkbox.setEnabled(True)
                    checkbox.setStyleSheet("font-size: 13px;")

                # Desktop & Dokumente-Buttons wieder aktivieren
                for btn_label, btn in self.quick_buttons.items():
                    if btn_label != label:
                        btn.setEnabled(True)

            self._on_sources_changed()

    def _add_folder_to_list(self, folder_path: Path):
        """Zentrale Methode zum Hinzufügen eines Ordners zur Liste"""
        if not folder_path:
            return

        # Prüfe ob bereits vorhanden
        if str(folder_path) in self.custom_sources:
            logger.info(f"Ordner bereits vorhanden: {folder_path}")
            return

        # Prüfe ob in Standard-Bibliotheken
        for lib_path in self.standard_libraries.values():
            if folder_path == lib_path:
                logger.info(f"Ordner ist bereits in Standard-Bibliotheken: {folder_path}")
                return

        # Hinzufügen
        self.custom_sources.append(str(folder_path))

        # Erstelle formatiertes List-Item mit Widget
        folder_name = folder_path.name or folder_path.parts[-1]
        parent_path = str(folder_path.parent)

        # List Item
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, str(folder_path))
        item.setToolTip(str(folder_path))

        # Custom Widget für schöne Darstellung
        widget = ClickableFrame(self.custom_list, item)
        widget.setMinimumHeight(40)
        widget.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 3px;
                padding: 2px;
            }
            QFrame:hover {
                background-color: #e8e8e8;
            }
        """)
        widget_layout = QHBoxLayout(widget)
        widget_layout.setContentsMargins(10, 8, 10, 8)

        # Icon + Ordnername (fett, Akzentfarbe)
        label = QLabel(f"📁 {folder_name}")
        label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; "
            f"color: {get_color('primary')}; background: transparent;"
        )
        widget_layout.addWidget(label)

        widget_layout.addStretch()

        # Pfad (klein, grau)
        path_label = QLabel(parent_path)
        path_label.setStyleSheet("font-size: 11px; color: #666; background: transparent;")
        widget_layout.addWidget(path_label)

        # Füge hinzu
        self.custom_list.addItem(item)
        self.custom_list.setItemWidget(item, widget)
        item.setSizeHint(widget.sizeHint())

        # Speichere Widget-Referenz für Selection-Handling
        self.custom_widgets[str(folder_path)] = (item, widget)

        logger.info(f"Eigener Ordner hinzugefügt: {folder_path}")
        self._on_sources_changed()

    def _remove_custom_folder(self):
        """Entfernt ausgewählten eigenen Ordner"""
        current_item = self.custom_list.currentItem()

        if current_item:
            # Hole vollständigen Pfad aus UserRole
            folder = current_item.data(Qt.ItemDataRole.UserRole)
            if folder in self.custom_sources:
                self.custom_sources.remove(folder)

            # Entferne Widget-Referenz
            if folder in self.custom_widgets:
                del self.custom_widgets[folder]

            self.custom_list.takeItem(self.custom_list.row(current_item))

            logger.info(f"Eigener Ordner entfernt: {folder}")
            self._on_sources_changed()

    def _on_selection_changed(self):
        """Wird aufgerufen wenn Selection sich ändert"""
        # Setze alle Widgets auf normalen Hintergrund
        for item, widget in self.custom_widgets.values():
            widget.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border-radius: 3px;
                    padding: 2px;
                }
                QFrame:hover {
                    background-color: #e8e8e8;
                }
            """)

        # Setze selected Widget auf grauen Hintergrund
        selected_items = self.custom_list.selectedItems()
        for selected_item in selected_items:
            # Finde das Widget für dieses Item
            folder_path = selected_item.data(Qt.ItemDataRole.UserRole)
            if folder_path in self.custom_widgets:
                item, widget = self.custom_widgets[folder_path]
                widget.setStyleSheet("""
                    QFrame {
                        background-color: #d0d0d0;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QFrame:hover {
                        background-color: #c0c0c0;
                    }
                """)

    def _on_library_changed(self):
        """Wird aufgerufen wenn Bibliotheken-Auswahl sich ändert"""
        # Prüfe ob irgendeine Bibliothek ausgewählt ist
        any_library_checked = any(cb.isChecked() for cb in self.library_checkboxes.values())

        # Wenn Bibliotheken ausgewählt sind: Home-Button deaktivieren
        if "🏠 Home" in self.quick_buttons:
            home_btn = self.quick_buttons["🏠 Home"]
            if any_library_checked:
                home_btn.setEnabled(False)
                # Wenn Home vorher aktiv war: deaktivieren
                if home_btn.isChecked():
                    home_btn.setChecked(False)
            else:
                home_btn.setEnabled(True)

        self._on_sources_changed()

    def _on_sources_changed(self):
        """Wird aufgerufen wenn Quellen sich ändern"""
        sources_str = self.selectedSources
        logger.info(f"Sources changed: {len(self.custom_sources)} custom, value: '{sources_str}'")
        self._sources_edit.setText(sources_str)  # Aktualisiert das Feld für wizard.field()
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        """Prüft ob mindestens eine Quelle ausgewählt wurde"""
        result = bool(self.selectedSources)
        logger.info(f"isComplete called: {result} (sources: '{self.selectedSources}')")
        return result

    # Properties für Wizard-Felder
    @property
    def selectedSources(self) -> str:
        """
        Gibt gewählte Quellen zurück (als String für QWizard)

        Returns:
            Komma-separierte Liste von Pfaden
        """
        sources = []

        # Standard-Bibliotheken
        for name, checkbox in self.library_checkboxes.items():
            if checkbox.isChecked():
                path = self.standard_libraries[name]
                sources.append(str(path))

        # Eigene Ordner
        sources.extend(self.custom_sources)

        return ",".join(sources) if sources else ""

    @property
    def excludePatterns(self) -> str:
        """
        Gibt Ausschluss-Muster zurück (als String für QWizard)

        Returns:
            Komma-separierte Liste von Patterns
        """
        return ",".join(self.exclude_patterns)

    def get_sources_list(self) -> List[str]:
        """
        Gibt Quellen als Liste zurück

        Returns:
            Liste von Pfaden
        """
        sources = []

        # Standard-Bibliotheken
        for name, checkbox in self.library_checkboxes.items():
            if checkbox.isChecked():
                path = self.standard_libraries[name]
                sources.append(str(path))

        # Eigene Ordner
        sources.extend(self.custom_sources)

        return sources

    def validatePage(self) -> bool:
        """Validiert Seite vor Weiter"""
        sources = self.get_sources_list()

        if not sources:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Keine Quellen gewählt",
                "Bitte wähle mindestens einen Ordner oder eine Bibliothek aus, "
                "die gesichert werden soll.",
            )
            return False

        logger.info(f"Quellen gewählt: {len(sources)} Ordner")
        for source in sources:
            logger.debug(f"  - {source}")

        return True

    def nextId(self) -> int:
        """Nächste Seite: Destination (Ziel-Auswahl)"""
        PAGE_DESTINATION = 3
        return PAGE_DESTINATION
