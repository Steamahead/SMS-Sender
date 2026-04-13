from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QWidget, QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal

from core.personalizer import Personalizer
from gui.styles import COLORS


class PreviewTable(QGroupBox):
    """Table showing recipients with personalized message preview."""

    def __init__(self, parent=None):
        super().__init__("Podglad odbiorcow", parent)
        self._numbers = []
        self._row_data = []
        self._headers = None
        self._template = ""
        self._checks = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["", "Numer", "Tresc"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 40)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._table.verticalHeader().setVisible(False)

        layout.addWidget(self._table)

    def update_data(self, numbers: list[str], row_data: list[list],
                    headers: list[str] | None, template: str):
        self._numbers = numbers
        self._row_data = row_data
        self._headers = headers
        self._template = template
        self._refresh()

    def update_template(self, template: str):
        self._template = template
        self._refresh()

    def get_selected_numbers(self) -> list[str]:
        selected = []
        for i, num in enumerate(self._numbers):
            if i < len(self._checks) and self._checks[i].isChecked():
                selected.append(num)
        return selected

    def _refresh(self):
        self._table.setRowCount(len(self._numbers))
        self._checks = []

        personalizer = None
        if self._template and self._row_data:
            personalizer = Personalizer(self._template, self._headers)

        for i, num in enumerate(self._numbers):
            # Checkbox
            cb = QCheckBox()
            cb.setChecked(True)
            self._checks.append(cb)

            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(i, 0, cb_widget)

            # Number
            num_item = QTableWidgetItem(num)
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(i, 1, num_item)

            # Personalized message
            if personalizer and i < len(self._row_data):
                msg = personalizer.render(self._row_data[i])
            else:
                msg = self._template
            msg_item = QTableWidgetItem(msg)
            msg_item.setFlags(msg_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(i, 2, msg_item)
