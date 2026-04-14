import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QIcon

from gui.styles import QSS
from gui.widgets.import_panel import ImportPanel
from gui.widgets.message_panel import MessagePanel
from gui.widgets.preview_table import PreviewTable
from gui.widgets.send_panel import SendPanel
from gui.widgets.history_view import HistoryView
from core.history import HistoryManager
from core.settings import Settings
from core.template_manager import TemplateManager


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
        self.setMinimumSize(800, 600)

        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._numbers = []
        self._skipped = []
        self._row_data = []
        self._headers = []

        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        self._data_dir = os.path.join(appdata, "SMSSender")

        os.makedirs(self._data_dir, exist_ok=True)

        self._history_manager = HistoryManager(os.path.join(self._data_dir, "history.db"))
        self._settings = Settings(os.path.join(self._data_dir, "settings.json"))
        self._template_manager = TemplateManager(os.path.join(self._data_dir, "templates.json"))

        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._build_send_tab()
        self._build_history_tab()

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Gotowy do pracy")

        if self._settings.window_x >= 0:
            self.setGeometry(
                self._settings.window_x, self._settings.window_y,
                self._settings.window_width, self._settings.window_height,
            )
        else:
            self.resize(self._settings.window_width, self._settings.window_height)

        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        paste_shortcut.activated.connect(self._on_global_paste)

    def _build_send_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        self._import_panel = ImportPanel(settings=self._settings)
        self._import_panel.numbers_changed.connect(self._on_numbers_changed)
        self._import_panel.headers_changed.connect(self._on_headers_changed)
        layout.addWidget(self._import_panel, stretch=0)

        self._message_panel = MessagePanel(template_manager=self._template_manager)
        self._message_panel.message_changed.connect(self._on_message_changed)
        layout.addWidget(self._message_panel, stretch=0)

        self._preview_table = PreviewTable()
        layout.addWidget(self._preview_table, stretch=1)

        self._send_panel = SendPanel()
        self._send_panel.sending_finished.connect(self._on_sending_finished)
        layout.addWidget(self._send_panel, stretch=0)

        self._tabs.addTab(tab, "Wysyłka")

    def _build_history_tab(self):
        self._history_view = HistoryView(self._history_manager)
        self._tabs.addTab(self._history_view, "Historia")
        self._tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        if index == 1:
            self._history_view.refresh()

    def _on_numbers_changed(self, numbers, skipped, row_data):
        self._numbers = numbers
        self._skipped = skipped
        self._row_data = row_data
        self._message_panel.set_recipient_count(len(numbers))
        self._preview_table.update_data(
            numbers, row_data, self._headers,
            self._message_panel.get_message(),
        )
        self._send_panel.set_ready(
            has_numbers=bool(numbers),
            has_message=bool(self._message_panel.get_message()),
        )
        self._send_panel.set_data(
            numbers, self._message_panel.get_message(),
            self._preview_table.get_selected_numbers,
        )
        n = len(numbers)
        if n == 1:
            word = "numer załadowany"
        elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
            word = "numery załadowane"
        else:
            word = "numerów załadowanych"
        self._status.showMessage(f"{n} {word}")

    def _on_headers_changed(self, headers):
        self._headers = headers
        self._message_panel.set_headers(headers)

    def _on_sending_finished(self, results):
        source = self._import_panel._lbl_file.text()
        self._history_manager.save_session(
            message=self._message_panel.get_message(),
            source_file=source,
            recipients=results,
        )
        self._status.showMessage("Wysyłka zakończona")

    def _on_message_changed(self, text):
        self._preview_table.update_template(text)
        self._send_panel.set_ready(
            has_numbers=bool(self._numbers),
            has_message=bool(text.strip()),
        )
        self._send_panel.set_data(
            self._numbers, text.strip(),
            self._preview_table.get_selected_numbers,
        )

    def closeEvent(self, event):
        geo = self.geometry()
        self._settings.window_width = geo.width()
        self._settings.window_height = geo.height()
        self._settings.window_x = geo.x()
        self._settings.window_y = geo.y()
        super().closeEvent(event)

    def _on_global_paste(self):
        from PySide6.QtWidgets import QApplication
        from core.clipboard_import import parse_clipboard_text
        from core.excel_importer import deduplicate_numbers

        if self._tabs.currentIndex() != 0:
            return
        if self._message_panel._editor.hasFocus():
            return

        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text or not text.strip():
            return

        valid, skipped = parse_clipboard_text(text)
        if not valid:
            return

        combined = self._numbers + valid
        combined, dup_count = deduplicate_numbers(combined)

        self._on_numbers_changed(combined, skipped, self._row_data)
        self._status.showMessage(
            f"Wklejono {len(valid)} numerów ({dup_count} duplikatów usuniętych)"
        )
