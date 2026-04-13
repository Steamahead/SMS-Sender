import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar,
)
from PySide6.QtCore import Qt

from gui.styles import QSS
from gui.widgets.import_panel import ImportPanel
from gui.widgets.message_panel import MessagePanel
from gui.widgets.preview_table import PreviewTable


class SMSSenderApp:
    """Main application entry point."""

    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setStyleSheet(QSS)

        self._window = MainWindow()

    def run(self):
        self._window.show()
        sys.exit(self._app.exec())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMS Sender")
        self.setMinimumSize(900, 700)

        self._numbers = []
        self._skipped = []
        self._row_data = []
        self._headers = []

        # Tabs
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._build_send_tab()
        self._build_history_tab()

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Gotowy")

    def _build_send_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Import panel
        self._import_panel = ImportPanel()
        self._import_panel.numbers_changed.connect(self._on_numbers_changed)
        self._import_panel.headers_changed.connect(self._on_headers_changed)
        layout.addWidget(self._import_panel)

        self._message_panel = MessagePanel()
        self._message_panel.message_changed.connect(self._on_message_changed)
        layout.addWidget(self._message_panel)

        self._preview_table = PreviewTable()
        layout.addWidget(self._preview_table)

        layout.addStretch()

        self._tabs.addTab(tab, "Wysylka")

    def _build_history_tab(self):
        tab = QWidget()
        self._tabs.addTab(tab, "Historia")

    def _on_numbers_changed(self, numbers, skipped, row_data):
        self._numbers = numbers
        self._skipped = skipped
        self._row_data = row_data
        self._message_panel.set_recipient_count(len(numbers))
        self._preview_table.update_data(
            numbers, row_data, self._headers,
            self._message_panel.get_message(),
        )
        self._status.showMessage(f"{len(numbers)} numerow zaladowanych")

    def _on_headers_changed(self, headers):
        self._headers = headers
        self._message_panel.set_headers(headers)

    def _on_message_changed(self, text):
        self._preview_table.update_template(text)
