from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QPushButton, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from gui.styles import COLORS


AI_STUDIO_URL = "https://aistudio.google.com/apikey"
GEMINI_DOCS_URL = "https://ai.google.dev/gemini-api/docs"


class SettingsTab(QWidget):
    """Settings tab. Currently hosts Gemini AI configuration."""

    settings_changed = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._build_ui()
        self._load_from_settings()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(14)

        title = QLabel("Asystent AI (Gemini)")
        title.setStyleSheet(
            f"font-size: 17px; font-weight: 600; color: {COLORS['text']};"
        )
        outer.addWidget(title)

        subtitle = QLabel(
            "Włącz „magiczną różdżkę” w polu treści SMS, aby poprawiać brzmienie "
            "wiadomości jednym kliknięciem. Asystent korzysta z modelu Google Gemini "
            "(darmowy plan z hojnym limitem). Klucz API jest zapisywany lokalnie na tym "
            "komputerze i nie jest nigdzie wysyłany poza Gemini."
        )
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['surface']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)

        lbl_key = QLabel("Klucz API Gemini")
        lbl_key.setStyleSheet(f"font-weight: 600; color: {COLORS['text']};")
        card_layout.addWidget(lbl_key)

        key_row = QHBoxLayout()
        key_row.setSpacing(6)

        self._input_key = QLineEdit()
        self._input_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._input_key.setPlaceholderText("Wklej klucz z aistudio.google.com/apikey")
        self._input_key.setMinimumHeight(32)
        key_row.addWidget(self._input_key)

        self._btn_toggle = QPushButton("Pokaż")
        self._btn_toggle.setFixedWidth(80)
        self._btn_toggle.setMinimumHeight(32)
        self._btn_toggle.setCheckable(True)
        self._btn_toggle.toggled.connect(self._on_toggle_visibility)
        key_row.addWidget(self._btn_toggle)

        card_layout.addLayout(key_row)

        link_row = QHBoxLayout()
        link = QLabel(
            f'<a href="{AI_STUDIO_URL}" style="color: {COLORS["accent"]};">'
            f"Pobierz darmowy klucz z Google AI Studio</a>"
        )
        link.setOpenExternalLinks(True)
        link.setStyleSheet("font-size: 12px;")
        link_row.addWidget(link)
        link_row.addStretch()
        card_layout.addLayout(link_row)

        self._chk_enabled = QCheckBox("Włącz asystenta AI w polu treści SMS")
        card_layout.addWidget(self._chk_enabled)

        action_row = QHBoxLayout()
        action_row.addStretch()

        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
        action_row.addWidget(self._lbl_status)

        self._btn_save = QPushButton("Zapisz ustawienia")
        self._btn_save.setProperty("class", "primary")
        self._btn_save.setMinimumHeight(34)
        self._btn_save.setMinimumWidth(150)
        self._btn_save.clicked.connect(self._on_save)
        action_row.addWidget(self._btn_save)

        card_layout.addLayout(action_row)

        outer.addWidget(card)

        instr_title = QLabel("Jak skonfigurować w 3 krokach")
        instr_title.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {COLORS['text']}; margin-top: 12px;"
        )
        outer.addWidget(instr_title)

        steps = QLabel(
            "<ol style='margin:0; padding-left: 20px;'>"
            "<li>Wejdź na <a href='" + AI_STUDIO_URL + "' style='color:" + COLORS['accent']
            + ";'>aistudio.google.com/apikey</a> i zaloguj się kontem Google.</li>"
            "<li>Kliknij „Create API key” — wygeneruj klucz dla nowego projektu lub istniejącego.</li>"
            "<li>Wklej klucz w pole powyżej, zaznacz „Włącz asystenta AI” i kliknij „Zapisz”.</li>"
            "</ol>"
            "<p style='margin-top: 10px;'>Po zapisaniu, w panelu treści SMS pojawi się "
            "przycisk różdżki — kliknięcie wyśle obecną treść do Gemini i pokaże trzy warianty "
            "do wyboru: <b>korekta</b>, <b>formalny</b>, <b>przyjazny</b>.</p>"
            "<p style='color:" + COLORS['text_secondary'] + ";'>Darmowy plan Gemini wystarczy "
            "do kilku tysięcy zapytań miesięcznie. Nie wysyłaj danych wrażliwych "
            "(numerów PESEL, danych medycznych) — treść SMS-a trafia do serwerów Google.</p>"
        )
        steps.setWordWrap(True)
        steps.setOpenExternalLinks(True)
        steps.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; line-height: 1.5;")
        outer.addWidget(steps)

        outer.addStretch()

    def _load_from_settings(self):
        self._input_key.setText(self._settings.gemini_api_key)
        self._chk_enabled.setChecked(self._settings.ai_enabled)

    def _on_toggle_visibility(self, checked: bool):
        self._input_key.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        self._btn_toggle.setText("Ukryj" if checked else "Pokaż")

    def _on_save(self):
        key = self._input_key.text().strip()
        enabled = self._chk_enabled.isChecked()

        if enabled and not key:
            self._lbl_status.setStyleSheet(f"color: {COLORS['error']}; font-size: 12px;")
            self._lbl_status.setText("Aby włączyć AI, wprowadź klucz API.")
            return

        self._settings.gemini_api_key = key
        self._settings.ai_enabled = enabled

        self._lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
        self._lbl_status.setText("✓ Zapisano")
        self.settings_changed.emit()

    def focus_api_key_field(self):
        """Public helper — called when user clicks wand without a key set."""
        self._lbl_status.setStyleSheet(f"color: {COLORS['accent']}; font-size: 12px;")
        self._lbl_status.setText("← Wprowadź klucz API, aby włączyć asystenta AI.")
        self._input_key.setFocus()
