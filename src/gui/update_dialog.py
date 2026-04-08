"""
Update-Dialog für Scrat-Backup
Zeigt verfügbare neue Version mit Changelog und Download-Button.
"""

import logging

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QHBoxLayout,
)

logger = logging.getLogger(__name__)


class UpdateDialog(QDialog):
    """
    Dialog der den Nutzer über eine neue Version informiert.
    Bietet direkten Download-Button (öffnet Browser) oder Schließen.
    """

    def __init__(
        self,
        latest_version: str,
        release_notes: str,
        download_url: str,
        release_url: str,
        current_version: str,
        parent=None,
    ):
        super().__init__(parent)
        self._download_url = download_url
        self._release_url = release_url
        self._setup_ui(latest_version, release_notes, current_version)

    def _setup_ui(self, latest_version: str, release_notes: str, current_version: str) -> None:
        self.setWindowTitle("Update verfügbar")
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        title = QLabel(f"🐿️ Scrat-Backup {latest_version} ist verfügbar!")
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        subtitle = QLabel(f"Du verwendest Version {current_version}.")
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)

        # Release Notes
        notes_label = QLabel("Was ist neu:")
        notes_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(notes_label)

        notes_browser = QTextBrowser()
        notes_browser.setMarkdown(release_notes or "_Keine Release Notes verfügbar._")
        notes_browser.setMaximumHeight(200)
        notes_browser.setOpenExternalLinks(True)
        layout.addWidget(notes_browser)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_later = QPushButton("Später")
        btn_later.clicked.connect(self.reject)
        btn_layout.addWidget(btn_later)

        btn_release = QPushButton("Release-Seite")
        btn_release.clicked.connect(self._open_release_page)
        btn_layout.addWidget(btn_release)

        btn_download = QPushButton("⬇ Jetzt herunterladen")
        btn_download.setDefault(True)
        btn_download.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; "
            "padding: 6px 16px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #106ebe; }"
        )
        btn_download.clicked.connect(self._open_download)
        btn_layout.addWidget(btn_download)

        layout.addLayout(btn_layout)

    def _open_download(self) -> None:
        import webbrowser
        webbrowser.open(self._download_url)
        self.accept()

    def _open_release_page(self) -> None:
        import webbrowser
        webbrowser.open(self._release_url)


def show_update_dialog(
    latest_version: str,
    release_notes: str,
    download_url: str,
    release_url: str,
    current_version: str,
    parent=None,
) -> None:
    """Zeigt den Update-Dialog – wird als Qt-Slot aufgerufen (im Hauptthread)."""
    dlg = UpdateDialog(
        latest_version=latest_version,
        release_notes=release_notes,
        download_url=download_url,
        release_url=release_url,
        current_version=current_version,
        parent=parent,
    )
    dlg.exec()
