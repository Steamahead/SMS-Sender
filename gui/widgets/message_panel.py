import os

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QInputDialog, QMessageBox,
)
from PySide6.QtCore import Signal

from gui.styles import COLORS


class MessagePanel(QGroupBox):
    """Panel for composing SMS message with templates and character counter."""

    MAX_CHARS = 320
    message_changed = Signal(str)

    def __init__(self, template_manager=None, parent=None):
        super().__init__("Tresc SMS", parent)
        self._template_manager = template_manager
        self._headers = []
        self._recipient_count = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Templates row
        row1 = QHBoxLayout()

        self._combo_templates = QComboBox()
        self._combo_templates.setMinimumWidth(200)
        self._combo_templates.addItem("-- Szablony --")
        self._combo_templates.currentIndexChanged.connect(self._on_template_selected)
        row1.addWidget(self._combo_templates)

        btn_save_tpl = QPushButton("Zapisz szablon")
        btn_save_tpl.clicked.connect(self._on_save_template)
        row1.addWidget(btn_save_tpl)

        btn_del_tpl = QPushButton("Usun szablon")
        btn_del_tpl.clicked.connect(self._on_delete_template)
        row1.addWidget(btn_del_tpl)

        row1.addStretch()
        layout.addLayout(row1)

        # Variables hint
        self._lbl_variables = QLabel("")
        self._lbl_variables.setProperty("class", "dim")
        self._lbl_variables.setWordWrap(True)
        layout.addWidget(self._lbl_variables)

        # Text editor
        self._editor = QTextEdit()
        self._editor.setMaximumHeight(100)
        self._editor.setPlaceholderText("Wpisz tresc wiadomosci...")
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

        # Char counter
        self._lbl_chars = QLabel("Znaki: 0/320 (1 SMS)")
        self._lbl_chars.setProperty("class", "dim")
        layout.addWidget(self._lbl_chars)

        # SMS count info
        self._lbl_sms_count = QLabel("")
        self._lbl_sms_count.setProperty("class", "dim")
        layout.addWidget(self._lbl_sms_count)

        self._refresh_templates()

    def set_headers(self, headers: list[str]):
        self._headers = headers
        if headers:
            vars_text = "Dostepne zmienne: " + ", ".join(
                f"{{{h}}}" for h in headers if h
            )
            self._lbl_variables.setText(vars_text)
        else:
            self._lbl_variables.setText("")

    def set_recipient_count(self, count: int):
        self._recipient_count = count
        self._update_sms_count()

    def get_message(self) -> str:
        return self._editor.toPlainText().strip()

    def _on_text_changed(self):
        text = self._editor.toPlainText()
        count = len(text)
        sms_parts = 1 if count <= 160 else 2
        color = COLORS["error"] if count > self.MAX_CHARS else COLORS["text_secondary"]

        self._lbl_chars.setText(f"Znaki: {count}/{self.MAX_CHARS} ({sms_parts} SMS)")
        self._lbl_chars.setStyleSheet(f"color: {color};")

        self._update_sms_count()
        self.message_changed.emit(text)

    def _update_sms_count(self):
        count = len(self._editor.toPlainText())
        recipients = self._recipient_count
        if recipients > 0 and count > 0:
            sms_parts = 1 if count <= 160 else 2
            total = recipients * sms_parts
            self._lbl_sms_count.setText(
                f"Odbiorcy: {recipients} x {sms_parts} SMS = {total} SMS-ow"
            )
        else:
            self._lbl_sms_count.setText("")

    def _on_template_selected(self, index: int):
        if index <= 0 or not self._template_manager:
            return
        name = self._combo_templates.currentText()
        content = self._template_manager.load(name)
        if content:
            self._editor.setPlainText(content)

    def _on_save_template(self):
        if not self._template_manager:
            return
        text = self._editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Pusta tresc", "Wpisz tresc szablonu")
            return

        name, ok = QInputDialog.getText(self, "Zapisz szablon", "Nazwa szablonu:")
        if ok and name.strip():
            self._template_manager.save(name.strip(), text)
            self._refresh_templates()

    def _on_delete_template(self):
        if not self._template_manager:
            return
        index = self._combo_templates.currentIndex()
        if index <= 0:
            return
        name = self._combo_templates.currentText()
        self._template_manager.delete(name)
        self._refresh_templates()

    def _refresh_templates(self):
        self._combo_templates.blockSignals(True)
        self._combo_templates.clear()
        self._combo_templates.addItem("-- Szablony --")
        if self._template_manager:
            for name in self._template_manager.list_names():
                self._combo_templates.addItem(name)
        self._combo_templates.blockSignals(False)
