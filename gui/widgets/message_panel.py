import os

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QInputDialog, QMessageBox, QDialog,
    QDialogButtonBox,
)
from PySide6.QtCore import Signal

from gui.styles import COLORS


class MessagePanel(QGroupBox):
    """Panel for composing SMS message with templates and character counter."""

    MAX_CHARS = 320
    message_changed = Signal(str)

    def __init__(self, template_manager=None, parent=None):
        super().__init__("Treść SMS", parent)
        self._template_manager = template_manager
        self._headers = []
        self._recipient_count = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self._combo_templates = QComboBox()
        self._combo_templates.setMinimumWidth(220)
        self._combo_templates.setEditable(True)
        self._combo_templates.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._combo_templates.lineEdit().setPlaceholderText("Wybierz lub wpisz nazwę szablonu...")
        self._combo_templates.addItem("")
        self._combo_templates.currentIndexChanged.connect(self._on_template_selected)
        row1.addWidget(self._combo_templates)

        btn_save_tpl = QPushButton("Zapisz")
        btn_save_tpl.clicked.connect(self._on_save_template)
        row1.addWidget(btn_save_tpl)

        btn_edit_tpl = QPushButton("Edytuj")
        btn_edit_tpl.clicked.connect(self._on_edit_template)
        row1.addWidget(btn_edit_tpl)

        btn_del_tpl = QPushButton("Usuń")
        btn_del_tpl.clicked.connect(self._on_delete_template)
        row1.addWidget(btn_del_tpl)

        row1.addStretch()
        layout.addLayout(row1)

        self._lbl_variables = QLabel("")
        self._lbl_variables.setProperty("class", "dim")
        self._lbl_variables.setWordWrap(True)
        layout.addWidget(self._lbl_variables)

        self._editor = QTextEdit()
        self._editor.setMinimumHeight(60)
        self._editor.setMaximumHeight(90)
        self._editor.setPlaceholderText("Wpisz treść wiadomości tutaj...")
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

        bottom_row = QHBoxLayout()

        self._lbl_chars = QLabel("Znaki: 0/320 (1 SMS)")
        self._lbl_chars.setProperty("class", "dim")
        bottom_row.addWidget(self._lbl_chars)

        bottom_row.addStretch()

        self._lbl_sms_count = QLabel("")
        self._lbl_sms_count.setProperty("class", "dim")
        bottom_row.addWidget(self._lbl_sms_count)

        layout.addLayout(bottom_row)

        self._refresh_templates()

    def set_headers(self, headers: list[str]):
        self._headers = headers
        if headers:
            vars_text = "Dostępne zmienne: " + ", ".join(
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

    def clear_message(self):
        self._editor.clear()

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
                f"Odbiorcy: {recipients}  |  Łącznie: {total} SMS"
            )
        elif recipients > 0:
            self._lbl_sms_count.setText(f"Odbiorcy: {recipients}")
        else:
            self._lbl_sms_count.setText("")

    def _on_template_selected(self, index: int):
        if index <= 0 or not self._template_manager:
            return
        name = self._combo_templates.itemText(index)
        content = self._template_manager.load(name)
        if content:
            self._editor.setPlainText(content)

    def _on_save_template(self):
        if not self._template_manager:
            return
        text = self._editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Pusta treść", "Wpisz treść szablonu przed zapisem.")
            return

        name = self._combo_templates.currentText().strip()
        if not name:
            name, ok = QInputDialog.getText(self, "Zapisz szablon", "Nazwa szablonu:")
            if not ok or not name.strip():
                return
            name = name.strip()

        existing = self._template_manager.list_names()
        if name in existing:
            reply = QMessageBox.question(
                self, "Nadpisać szablon?",
                f"Szablon „{name}” już istnieje. Nadpisać go nową treścią?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._template_manager.save(name, text)
        self._refresh_templates()
        self._combo_templates.setCurrentText(name)

    def _on_edit_template(self):
        if not self._template_manager:
            return
        name = self._combo_templates.currentText().strip()
        if not name or name not in self._template_manager.list_names():
            QMessageBox.information(
                self, "Wybierz szablon",
                "Najpierw wybierz szablon do edycji z listy.",
            )
            return

        content = self._template_manager.load(name) or ""
        new_text = self._open_edit_dialog(name, content)
        if new_text is None:
            return

        self._template_manager.save(name, new_text)
        if self._combo_templates.currentText().strip() == name:
            self._editor.setPlainText(new_text)

    def _open_edit_dialog(self, name: str, content: str) -> str | None:
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Edytuj szablon — {name}")
        dlg.resize(520, 280)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        lbl = QLabel(f"Treść szablonu „{name}”:")
        layout.addWidget(lbl)

        editor = QTextEdit()
        editor.setPlainText(content)
        editor.setMinimumHeight(160)
        layout.addWidget(editor)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Zapisz")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Anuluj")
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None

        new_text = editor.toPlainText().strip()
        if not new_text:
            QMessageBox.warning(self, "Pusta treść", "Treść szablonu nie może być pusta.")
            return None
        return new_text

    def _on_delete_template(self):
        if not self._template_manager:
            return
        name = self._combo_templates.currentText().strip()
        if not name or name not in self._template_manager.list_names():
            return
        reply = QMessageBox.question(
            self, "Usunąć szablon?",
            f"Czy na pewno usunąć szablon „{name}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._template_manager.delete(name)
        self._refresh_templates()

    def _refresh_templates(self):
        current = self._combo_templates.currentText().strip()
        self._combo_templates.blockSignals(True)
        self._combo_templates.clear()
        self._combo_templates.addItem("")
        if self._template_manager:
            for name in self._template_manager.list_names():
                self._combo_templates.addItem(name)
        if current and current in (self._template_manager.list_names() if self._template_manager else []):
            self._combo_templates.setCurrentText(current)
        else:
            self._combo_templates.setCurrentIndex(0)
            self._combo_templates.lineEdit().clear()
        self._combo_templates.blockSignals(False)
