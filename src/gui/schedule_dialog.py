"""
Schedule-Dialog für Scrat-Backup
Dialog zum Erstellen und Bearbeiten von Zeitplänen
"""

import logging
from datetime import time
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.scheduler import Schedule, ScheduleFrequency, Weekday

logger = logging.getLogger(__name__)


class ScheduleDialog(QDialog):
    """
    Dialog zum Erstellen/Bearbeiten von Zeitplänen

    Features:
    - Name-Eingabe
    - Frequenz-Auswahl (Daily, Weekly, Monthly, Startup, Shutdown)
    - Dynamische Felder basierend auf Frequenz
    - Zeit-Picker für tägliche/wöchentliche/monatliche Backups
    - Wochentage-Auswahl für wöchentliche Backups
    - Tag-im-Monat für monatliche Backups
    - Quellen-Auswahl (Multi-Select)
    - Ziel-Auswahl
    - Backup-Typ (Full/Incremental)
    - Validierung
    """

    def __init__(self, parent: Optional[QWidget] = None, schedule: Optional[Schedule] = None):
        """
        Initialisiert Dialog

        Args:
            parent: Parent-Widget
            schedule: Zu bearbeitender Zeitplan (None = Neu erstellen)
        """
        super().__init__(parent)

        self.schedule = schedule
        self.is_edit_mode = schedule is not None

        self._setup_ui()
        self._connect_signals()

        # Lade Daten wenn im Edit-Modus
        if self.is_edit_mode:
            self._load_schedule_data()

        logger.debug(f"ScheduleDialog initialisiert (Edit: {self.is_edit_mode})")

    def _setup_ui(self) -> None:
        """Erstellt UI-Komponenten"""
        title = "Zeitplan bearbeiten" if self.is_edit_mode else "Zeitplan erstellen"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"⏰ {title}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Form
        form = QFormLayout()
        form.setSpacing(10)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("z.B. 'Tägliches Backup 10:00'")
        form.addRow("Name:", self.name_edit)

        # Frequenz
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItem("📅 Täglich", ScheduleFrequency.DAILY)
        self.frequency_combo.addItem("📆 Wöchentlich", ScheduleFrequency.WEEKLY)
        self.frequency_combo.addItem("🗓️ Monatlich", ScheduleFrequency.MONTHLY)
        self.frequency_combo.addItem("🚀 Bei System-Start", ScheduleFrequency.STARTUP)
        self.frequency_combo.addItem("🔌 Bei System-Herunterfahren", ScheduleFrequency.SHUTDOWN)
        form.addRow("Häufigkeit:", self.frequency_combo)

        layout.addLayout(form)

        # Dynamische Felder (abhängig von Frequenz)
        self.time_group = self._create_time_group()
        self.weekdays_group = self._create_weekdays_group()
        self.monthly_group = self._create_monthly_group()

        layout.addWidget(self.time_group)
        layout.addWidget(self.weekdays_group)
        layout.addWidget(self.monthly_group)

        # Quellen & Ziel
        layout.addWidget(self._create_sources_group())
        layout.addWidget(self._create_destination_group())

        # Backup-Typ
        backup_layout = QFormLayout()
        self.backup_type_combo = QComboBox()
        self.backup_type_combo.addItem("📦 Inkrementell", "incremental")
        self.backup_type_combo.addItem("💾 Vollbackup", "full")
        backup_layout.addRow("Backup-Typ:", self.backup_type_combo)
        layout.addLayout(backup_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Initial: Felder aktualisieren
        self._update_visible_fields()

    def _create_time_group(self) -> QGroupBox:
        """Erstellt Zeit-Auswahl-Gruppe"""
        group = QGroupBox("🕐 Uhrzeit")
        layout = QFormLayout()

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(time(10, 0))  # Default: 10:00
        layout.addRow("Zeit:", self.time_edit)

        group.setLayout(layout)
        return group

    def _create_weekdays_group(self) -> QGroupBox:
        """Erstellt Wochentage-Auswahl-Gruppe"""
        group = QGroupBox("📆 Wochentage")
        layout = QHBoxLayout()

        self.weekday_checkboxes = {}
        weekdays = [
            (Weekday.MONDAY, "Mo"),
            (Weekday.TUESDAY, "Di"),
            (Weekday.WEDNESDAY, "Mi"),
            (Weekday.THURSDAY, "Do"),
            (Weekday.FRIDAY, "Fr"),
            (Weekday.SATURDAY, "Sa"),
            (Weekday.SUNDAY, "So"),
        ]

        for weekday, label in weekdays:
            checkbox = QCheckBox(label)
            self.weekday_checkboxes[weekday] = checkbox
            layout.addWidget(checkbox)

        group.setLayout(layout)
        return group

    def _create_monthly_group(self) -> QGroupBox:
        """Erstellt Monatliche-Auswahl-Gruppe"""
        group = QGroupBox("🗓️ Tag im Monat")
        layout = QFormLayout()

        self.day_of_month_spin = QSpinBox()
        self.day_of_month_spin.setRange(1, 31)
        self.day_of_month_spin.setValue(1)
        self.day_of_month_spin.setSuffix(". Tag")
        layout.addRow("Tag:", self.day_of_month_spin)

        group.setLayout(layout)
        return group

    def _create_sources_group(self) -> QGroupBox:
        """Erstellt Quellen-Auswahl-Gruppe"""
        group = QGroupBox("📁 Quellen")
        layout = QVBoxLayout()

        info = QLabel("Wähle die Quellen aus, die gesichert werden sollen:")
        info.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info)

        self.sources_list = QListWidget()
        self.sources_list.setMaximumHeight(100)

        # TODO: Lade Quellen aus Config
        # Für jetzt: Beispiel-Daten
        example_sources = [
            (1, "C:\\Benutzer\\Documents"),
            (2, "C:\\Benutzer\\Pictures"),
            (3, "D:\\Projekte"),
        ]

        for source_id, source_path in example_sources:
            item = QListWidgetItem(source_path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)  # Default: alle ausgewählt
            item.setData(Qt.ItemDataRole.UserRole, source_id)
            self.sources_list.addItem(item)

        layout.addWidget(self.sources_list)

        group.setLayout(layout)
        return group

    def _create_destination_group(self) -> QGroupBox:
        """Erstellt Ziel-Auswahl-Gruppe"""
        group = QGroupBox("💾 Ziel")
        layout = QFormLayout()

        self.destination_combo = QComboBox()

        # TODO: Lade Ziele aus Config
        # Für jetzt: Beispiel-Daten
        example_destinations = [
            (1, "USB-Laufwerk E:\\Backups"),
            (2, "NAS (SMB) - \\\\192.168.1.100\\Backups"),
            (3, "Cloud (Rclone) - Google Drive"),
        ]

        for dest_id, dest_name in example_destinations:
            self.destination_combo.addItem(dest_name, dest_id)

        layout.addRow("Backup-Ziel:", self.destination_combo)

        group.setLayout(layout)
        return group

    def _connect_signals(self) -> None:
        """Verbindet Signals"""
        self.frequency_combo.currentIndexChanged.connect(self._update_visible_fields)

    def _update_visible_fields(self) -> None:
        """Aktualisiert Sichtbarkeit der Felder basierend auf Frequenz"""
        frequency: ScheduleFrequency = self.frequency_combo.currentData()

        # Zeit-Gruppe: Nur bei Daily, Weekly, Monthly
        show_time = frequency in [
            ScheduleFrequency.DAILY,
            ScheduleFrequency.WEEKLY,
            ScheduleFrequency.MONTHLY,
        ]
        self.time_group.setVisible(show_time)

        # Wochentage: Nur bei Weekly
        self.weekdays_group.setVisible(frequency == ScheduleFrequency.WEEKLY)

        # Monatlich: Nur bei Monthly
        self.monthly_group.setVisible(frequency == ScheduleFrequency.MONTHLY)

    def _load_schedule_data(self) -> None:
        """Lädt Daten des zu bearbeitenden Zeitplans"""
        if not self.schedule:
            return

        # Name
        self.name_edit.setText(self.schedule.name)

        # Frequenz
        for i in range(self.frequency_combo.count()):
            if self.frequency_combo.itemData(i) == self.schedule.frequency:
                self.frequency_combo.setCurrentIndex(i)
                break

        # Zeit
        if self.schedule.time:
            self.time_edit.setTime(self.schedule.time)

        # Wochentage
        for weekday, checkbox in self.weekday_checkboxes.items():
            checkbox.setChecked(weekday in self.schedule.weekdays)

        # Tag im Monat
        if self.schedule.day_of_month:
            self.day_of_month_spin.setValue(self.schedule.day_of_month)

        # Quellen (TODO: Markiere ausgewählte)
        # ...

        # Ziel
        for i in range(self.destination_combo.count()):
            if self.destination_combo.itemData(i) == self.schedule.destination_id:
                self.destination_combo.setCurrentIndex(i)
                break

        # Backup-Typ
        for i in range(self.backup_type_combo.count()):
            if self.backup_type_combo.itemData(i) == self.schedule.backup_type:
                self.backup_type_combo.setCurrentIndex(i)
                break

    def _accept(self) -> None:
        """Validiert und akzeptiert Dialog"""
        # Validierung
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ungültige Eingabe", "Bitte gib einen Namen ein.")
            return

        frequency: ScheduleFrequency = self.frequency_combo.currentData()

        # Validierung: Wochentage bei Weekly
        if frequency == ScheduleFrequency.WEEKLY:
            selected_weekdays = [wd for wd, cb in self.weekday_checkboxes.items() if cb.isChecked()]
            if not selected_weekdays:
                QMessageBox.warning(
                    self,
                    "Ungültige Eingabe",
                    "Bitte wähle mindestens einen Wochentag aus.",
                )
                return

        # Validierung: Quellen
        selected_sources = self._get_selected_sources()
        if not selected_sources:
            QMessageBox.warning(
                self, "Ungültige Eingabe", "Bitte wähle mindestens eine Quelle aus."
            )
            return

        # Alles OK
        self.accept()

    def _get_selected_sources(self) -> List[int]:
        """Holt ausgewählte Quellen-IDs"""
        selected = []
        for i in range(self.sources_list.count()):
            item = self.sources_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                source_id = item.data(Qt.ItemDataRole.UserRole)
                selected.append(source_id)
        return selected

    def get_schedule(self) -> Schedule:
        """
        Erstellt Schedule-Objekt aus Dialog-Daten

        Returns:
            Schedule-Objekt
        """
        frequency: ScheduleFrequency = self.frequency_combo.currentData()

        # Zeit (nur bei Daily/Weekly/Monthly)
        schedule_time = None
        if frequency in [
            ScheduleFrequency.DAILY,
            ScheduleFrequency.WEEKLY,
            ScheduleFrequency.MONTHLY,
        ]:
            qt_time = self.time_edit.time()
            schedule_time = time(qt_time.hour(), qt_time.minute())

        # Wochentage (nur bei Weekly)
        weekdays = []
        if frequency == ScheduleFrequency.WEEKLY:
            weekdays = [wd for wd, cb in self.weekday_checkboxes.items() if cb.isChecked()]

        # Tag im Monat (nur bei Monthly)
        day_of_month = None
        if frequency == ScheduleFrequency.MONTHLY:
            day_of_month = self.day_of_month_spin.value()

        # Quellen
        source_ids = self._get_selected_sources()

        # Ziel
        destination_id = self.destination_combo.currentData()

        # Backup-Typ
        backup_type = self.backup_type_combo.currentData()

        # ID: Behalte alte ID bei Edit, None bei Neu
        schedule_id = self.schedule.id if self.schedule else None

        return Schedule(
            id=schedule_id,
            name=self.name_edit.text().strip(),
            enabled=True,  # Neu erstellte Zeitpläne sind aktiv
            frequency=frequency,
            time=schedule_time,
            weekdays=weekdays,
            day_of_month=day_of_month,
            source_ids=source_ids,
            destination_id=destination_id,
            backup_type=backup_type,
        )
