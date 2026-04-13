from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QSplitter,
)
from PySide6.QtCore import Qt

from core.history import HistoryManager


class HistoryView(QWidget):
    """View for browsing SMS sending history."""

    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self._hm = history_manager
        self._session_ids = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Sessions table
        sessions_group = QGroupBox("Sesje wysylki")
        sessions_layout = QVBoxLayout(sessions_group)

        self._sessions_table = QTableWidget()
        self._sessions_table.setColumnCount(5)
        self._sessions_table.setHorizontalHeaderLabels([
            "Data", "Plik", "Tresc", "Wyslano", "Bledy"
        ])
        self._sessions_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._sessions_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._sessions_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self._sessions_table.verticalHeader().setVisible(False)
        self._sessions_table.currentCellChanged.connect(self._on_session_selected)
        sessions_layout.addWidget(self._sessions_table)

        splitter.addWidget(sessions_group)

        # Session details
        details_group = QGroupBox("Szczegoly sesji")
        details_layout = QVBoxLayout(details_group)

        self._details_table = QTableWidget()
        self._details_table.setColumnCount(3)
        self._details_table.setHorizontalHeaderLabels(["Numer", "Status", "Blad"])
        self._details_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._details_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._details_table.verticalHeader().setVisible(False)
        details_layout.addWidget(self._details_table)

        splitter.addWidget(details_group)

        layout.addWidget(splitter)

    def refresh(self):
        sessions = self._hm.list_sessions()
        self._sessions_table.setRowCount(len(sessions))
        self._session_ids = []

        for i, s in enumerate(sessions):
            self._session_ids.append(s["id"])

            date_item = QTableWidgetItem(s["created_at"][:19].replace("T", " "))
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 0, date_item)

            file_item = QTableWidgetItem(s["source_file"])
            file_item.setFlags(file_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 1, file_item)

            msg_item = QTableWidgetItem(s["message"][:60])
            msg_item.setFlags(msg_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 2, msg_item)

            sent_item = QTableWidgetItem(str(s["sent"]))
            sent_item.setFlags(sent_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 3, sent_item)

            err_item = QTableWidgetItem(str(s["errors"]))
            err_item.setFlags(err_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 4, err_item)

    def _on_session_selected(self, row, col, prev_row, prev_col):
        if row < 0 or row >= len(self._session_ids):
            return

        session = self._hm.get_session(self._session_ids[row])
        if not session:
            return

        recipients = session["recipients"]
        self._details_table.setRowCount(len(recipients))

        for i, r in enumerate(recipients):
            num_item = QTableWidgetItem(r["number"])
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._details_table.setItem(i, 0, num_item)

            status_item = QTableWidgetItem(r["status"])
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._details_table.setItem(i, 1, status_item)

            error_item = QTableWidgetItem(r.get("error", "") or "")
            error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._details_table.setItem(i, 2, error_item)
