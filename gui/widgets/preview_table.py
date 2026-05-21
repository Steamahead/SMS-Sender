from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QWidget, QHBoxLayout,
    QPushButton, QSizePolicy, QLabel, QLineEdit,
)
from PySide6.QtCore import Qt, Signal

from core.personalizer import Personalizer
from core.excel_importer import validate_phone_number, deduplicate_numbers
from gui.styles import COLORS


class PreviewTable(QGroupBox):
    """Table showing recipients with personalized message preview."""

    numbers_changed_locally = Signal(list)
    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Podgląd odbiorców", parent)
        self._numbers = []
        self._row_data = []
        self._headers = None
        self._template = ""
        self._checks = []
        self._check_states = {}  # number -> bool, preserves checkbox state
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # Manual number entry row
        add_row = QHBoxLayout()
        add_row.setSpacing(6)

        self._input_number = QLineEdit()
        self._input_number.setPlaceholderText("Wpisz numer telefonu...")
        self._input_number.returnPressed.connect(self._on_add_number)
        add_row.addWidget(self._input_number)

        btn_add = QPushButton("Dodaj")
        btn_add.clicked.connect(self._on_add_number)
        add_row.addWidget(btn_add)

        layout.addLayout(add_row)

        # Select all / deselect all + counter
        btn_row = QHBoxLayout()
        btn_select_all = QPushButton("Zaznacz wszystkie")
        btn_select_all.clicked.connect(self._select_all)
        btn_row.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("Odznacz wszystkie")
        btn_deselect_all.clicked.connect(self._deselect_all)
        btn_row.addWidget(btn_deselect_all)

        self._btn_clear = QPushButton("Wyczyść listę")
        self._btn_clear.setToolTip("Usuń wszystkie numery i resetuj plik importu")
        self._btn_clear.clicked.connect(self.clear_requested.emit)
        btn_row.addWidget(self._btn_clear)

        btn_row.addStretch()

        self._lbl_count = QLabel("")
        self._lbl_count.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; font-size: 13px;")
        btn_row.addWidget(self._lbl_count)

        layout.addLayout(btn_row)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["", "Numer", "Gotowa treść", ""])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 40)
        self._table.setColumnWidth(3, 36)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.setMinimumHeight(350)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout.addWidget(self._table)

    def update_data(self, numbers: list[str], row_data: list[list],
                    headers: list[str] | None, template: str):
        self._numbers = numbers
        self._row_data = row_data
        self._headers = headers
        self._template = template
        # New data = reset check states (all checked)
        self._check_states = {num: True for num in numbers}
        self._refresh()

    def update_template(self, template: str):
        """Update only the message template — preserves checkbox states.
        Re-renders only the 'Gotowa treść' column without rebuilding row widgets."""
        self._template = template
        self._render_message_column()

    def _render_message_column(self):
        personalizer = None
        if self._template and self._row_data:
            personalizer = Personalizer(self._template, self._headers)

        for i, num in enumerate(self._numbers):
            if personalizer and i < len(self._row_data):
                msg = personalizer.render(self._row_data[i])
            else:
                msg = self._template

            item = self._table.item(i, 2)
            if item is None:
                item = QTableWidgetItem(msg)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(i, 2, item)
            else:
                item.setText(msg)

    def get_selected_numbers(self) -> list[str]:
        selected = []
        for i, num in enumerate(self._numbers):
            if i < len(self._checks) and self._checks[i].isChecked():
                selected.append(num)
        return selected

    def _save_check_states(self):
        """Save current checkbox states before refresh."""
        for i, num in enumerate(self._numbers):
            if i < len(self._checks):
                self._check_states[num] = self._checks[i].isChecked()

    def _select_all(self):
        for cb in self._checks:
            cb.setChecked(True)

    def _deselect_all(self):
        for cb in self._checks:
            cb.setChecked(False)

    def _on_add_number(self):
        raw = self._input_number.text().strip()
        if not raw:
            return

        is_valid, normalized, reason = validate_phone_number(raw)
        if not is_valid:
            self._input_number.setStyleSheet(f"border: 1px solid {COLORS['error']};")
            return

        self._input_number.setStyleSheet("")
        self._input_number.clear()

        if normalized in self._numbers:
            return  # already on list

        self._numbers.append(normalized)
        self._check_states[normalized] = True
        self._refresh()
        self.numbers_changed_locally.emit(list(self._numbers))

    def _on_remove_number(self, index: int):
        if index < 0 or index >= len(self._numbers):
            return
        self._save_check_states()
        num = self._numbers.pop(index)
        if index < len(self._row_data):
            self._row_data.pop(index)
        self._check_states.pop(num, None)
        self._refresh()
        self.numbers_changed_locally.emit(list(self._numbers))

    def _refresh(self):
        count = len(self._numbers)
        self._lbl_count.setText(f"Liczba numerów: {count}" if count > 0 else "")
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(count)
        self._checks = []

        personalizer = None
        if self._template and self._row_data:
            personalizer = Personalizer(self._template, self._headers)

        for i, num in enumerate(self._numbers):
            cb = QCheckBox()
            cb.setChecked(self._check_states.get(num, True))
            self._checks.append(cb)

            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(i, 0, cb_widget)

            num_item = QTableWidgetItem(num)
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            num_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 1, num_item)

            if personalizer and i < len(self._row_data):
                msg = personalizer.render(self._row_data[i])
            else:
                msg = self._template

            msg_item = QTableWidgetItem(msg)
            msg_item.setFlags(msg_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(i, 2, msg_item)

            btn_remove = QPushButton("✕")
            btn_remove.setFlat(True)
            btn_remove.setFixedSize(26, 22)
            btn_remove.setToolTip("Usuń numer z listy")
            btn_remove.setStyleSheet(
                f"QPushButton {{ color: {COLORS['text_dim']}; border: none; "
                f"font-weight: bold; font-size: 14px; background: transparent; }} "
                f"QPushButton:hover {{ color: {COLORS['error']}; }}"
            )
            btn_remove.clicked.connect(lambda _, idx=i: self._on_remove_number(idx))
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.addWidget(btn_remove)
            btn_layout.setAlignment(Qt.AlignCenter)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(i, 3, btn_widget)

        self._table.setUpdatesEnabled(True)
