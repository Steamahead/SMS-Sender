from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QSplitter, QDialog, QLabel, QTextEdit,
    QPushButton, QMessageBox,
)
from PySide6.QtCore import Qt

from core.history import HistoryManager
from gui.styles import COLORS


class HistoryView(QWidget):
    """View for browsing SMS sending history."""

    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self._hm = history_manager
        self._session_ids = []
        self._sessions_cache = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        sessions_group = QGroupBox("Sesje wysyłek")
        sessions_layout = QVBoxLayout(sessions_group)
        sessions_layout.setContentsMargins(8, 8, 8, 8)

        self._sessions_table = QTableWidget()
        self._sessions_table.setColumnCount(5)
        self._sessions_table.setHorizontalHeaderLabels([
            "Data", "Źródło", "Treść", "Wysłano", "Błędy"
        ])
        self._sessions_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._sessions_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
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
        self._sessions_table.setAlternatingRowColors(True)
        self._sessions_table.setShowGrid(False)
        self._sessions_table.currentCellChanged.connect(self._on_session_selected)
        self._sessions_table.cellDoubleClicked.connect(self._on_session_double_clicked)
        sessions_layout.addWidget(self._sessions_table)

        hint = QLabel("💡 Kliknij dwukrotnie wiersz, aby zobaczyć pełną treść SMS-a")
        hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        sessions_layout.addWidget(hint)

        actions_row = QHBoxLayout()
        self._btn_delete = QPushButton("Usuń zaznaczoną sesję")
        self._btn_delete.setToolTip("Trwale usuwa zaznaczoną sesję (dane osobowe)")
        self._btn_delete.clicked.connect(self._on_delete_session)
        actions_row.addWidget(self._btn_delete)

        self._btn_clear_all = QPushButton("Wyczyść całą historię")
        self._btn_clear_all.clicked.connect(self._on_clear_all)
        actions_row.addWidget(self._btn_clear_all)
        actions_row.addStretch()
        sessions_layout.addLayout(actions_row)

        splitter.addWidget(sessions_group)

        details_group = QGroupBox("Szczegóły sesji")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(8, 8, 8, 8)

        self._details_table = QTableWidget()
        self._details_table.setColumnCount(4)
        self._details_table.setHorizontalHeaderLabels(
            ["Numer telefonu", "Godzina", "Status", "Szczegóły błędu"]
        )
        self._details_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._details_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._details_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self._details_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self._details_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._details_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )
        self._details_table.verticalHeader().setVisible(False)
        self._details_table.setAlternatingRowColors(True)
        self._details_table.setShowGrid(False)
        details_layout.addWidget(self._details_table)

        splitter.addWidget(details_group)

        splitter.setSizes([400, 300])
        layout.addWidget(splitter)

    def refresh(self):
        sessions = self._hm.list_sessions()
        self._sessions_cache = sessions
        self._sessions_table.setRowCount(len(sessions))
        self._session_ids = []

        for i, s in enumerate(sessions):
            self._session_ids.append(s["id"])

            date_text = s["created_at"][:19].replace("T", " ")
            file_text = s["source_file"] or ""
            msg_full = s["message"] or ""
            msg_short = (msg_full[:140] + "…") if len(msg_full) > 140 else msg_full

            for col, (text, tooltip) in enumerate([
                (date_text, date_text),
                (file_text, file_text),
                (msg_short, msg_full),
            ]):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if tooltip:
                    item.setToolTip(tooltip)
                self._sessions_table.setItem(i, col, item)

            for col, value in [(3, str(s["sent"])), (4, str(s["errors"]))]:
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                self._sessions_table.setItem(i, col, item)

    def _current_session_id(self):
        row = self._sessions_table.currentRow()
        if 0 <= row < len(self._session_ids):
            return self._session_ids[row]
        return None

    def _on_delete_session(self):
        sid = self._current_session_id()
        if sid is None:
            QMessageBox.information(self, "Brak wyboru", "Najpierw zaznacz sesję do usunięcia.")
            return
        resp = QMessageBox.question(
            self, "Usuń sesję",
            "Trwale usunąć zaznaczoną sesję z historii? Tej operacji nie można cofnąć.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._hm.delete_session(sid)
            self._details_table.setRowCount(0)
            self.refresh()

    def _on_clear_all(self):
        if not self._session_ids:
            return
        resp = QMessageBox.question(
            self, "Wyczyść historię",
            "Trwale usunąć CAŁĄ historię wysyłek (wszystkie numery i treści)? "
            "Tej operacji nie można cofnąć.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._hm.clear_all()
            self._details_table.setRowCount(0)
            self.refresh()

    def _on_session_double_clicked(self, row: int, col: int):
        if row < 0 or row >= len(self._sessions_cache):
            return
        s = self._sessions_cache[row]
        dlg = SessionDetailsDialog(s, self)
        dlg.exec()

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

            time_item = QTableWidgetItem(r.get("time", "") or "")
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            time_item.setTextAlignment(Qt.AlignCenter)
            self._details_table.setItem(i, 1, time_item)

            status_item = QTableWidgetItem(r["status"])
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._details_table.setItem(i, 2, status_item)

            error_item = QTableWidgetItem(r.get("error", "") or "")
            error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._details_table.setItem(i, 3, error_item)


class SessionDetailsDialog(QDialog):
    """Modal showing the full SMS content + metadata for a history session."""

    def __init__(self, session: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Szczegóły wysyłki")
        self.setModal(True)
        self.resize(560, 380)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg']}; }}")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(12)

        date = (session.get("created_at") or "")[:19].replace("T", " ")
        source = session.get("source_file") or "—"
        message = session.get("message") or ""

        meta = QLabel(
            f"<table style='font-size:13px;'>"
            f"<tr><td style='color:{COLORS['text_secondary']}; padding-right:14px;'>Data:</td>"
            f"<td><b>{date}</b></td></tr>"
            f"<tr><td style='color:{COLORS['text_secondary']}; padding-right:14px;'>Źródło:</td>"
            f"<td>{source}</td></tr>"
            f"<tr><td style='color:{COLORS['text_secondary']}; padding-right:14px;'>Wysłano:</td>"
            f"<td>{session.get('sent', 0)} · błędy: {session.get('errors', 0)}</td></tr>"
            f"</table>"
        )
        meta.setTextFormat(Qt.TextFormat.RichText)
        outer.addWidget(meta)

        lbl_msg = QLabel("Treść SMS-a")
        lbl_msg.setStyleSheet(f"font-weight: 600; color: {COLORS['text']}; margin-top: 4px;")
        outer.addWidget(lbl_msg)

        editor = QTextEdit()
        editor.setPlainText(message)
        editor.setReadOnly(True)
        editor.setStyleSheet(
            f"QTextEdit {{ background-color: {COLORS['surface']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 6px; "
            f"padding: 10px; font-size: 13px; color: {COLORS['text']}; }}"
        )
        outer.addWidget(editor, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("Zamknij")
        btn_close.setMinimumWidth(100)
        btn_close.setMinimumHeight(32)
        btn_close.setDefault(True)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        outer.addLayout(btn_row)
