from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QPushButton, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from gui.styles import COLORS
from core.ai_refine import detect_provider, PROVIDER_LABELS


AI_STUDIO_URL = "https://aistudio.google.com/apikey"
GEMINI_DOCS_URL = "https://ai.google.dev/gemini-api/docs"
OPENAI_KEYS_URL = "https://platform.openai.com/api-keys"
ANTHROPIC_KEYS_URL = "https://console.anthropic.com/settings/keys"


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

        title = QLabel("Asystent AI")
        title.setStyleSheet(
            f"font-size: 17px; font-weight: 600; color: {COLORS['text']};"
        )
        outer.addWidget(title)

        subtitle = QLabel(
            "Włącz „magiczną różdżkę” w polu treści SMS, aby poprawiać brzmienie "
            "wiadomości jednym kliknięciem. Asystent korzysta z zewnętrznego modelu LLM — "
            "domyślnie polecamy <b>Google Gemini</b> (darmowy plan z hojnym limitem), ale "
            "możesz wkleić klucz API dowolnego z obsługiwanych dostawców: "
            "<b>Google Gemini</b>, <b>OpenAI</b> lub <b>Anthropic Claude</b>. Aplikacja "
            "rozpozna dostawcę automatycznie po formacie klucza. Klucz jest zapisywany "
            "lokalnie na tym komputerze i nie jest nigdzie wysyłany poza wybranego dostawcę."
        )
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        subtitle.setWordWrap(True)
        subtitle.setTextFormat(Qt.TextFormat.RichText)
        outer.addWidget(subtitle)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['surface']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)

        lbl_key = QLabel("Klucz API")
        lbl_key.setStyleSheet(f"font-weight: 600; color: {COLORS['text']};")
        card_layout.addWidget(lbl_key)

        key_row = QHBoxLayout()
        key_row.setSpacing(6)

        self._input_key = QLineEdit()
        self._input_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._input_key.setPlaceholderText("Wklej klucz Gemini, OpenAI lub Anthropic…")
        self._input_key.setMinimumHeight(32)
        self._input_key.textChanged.connect(self._on_key_changed)
        key_row.addWidget(self._input_key)

        self._btn_toggle = QPushButton("Pokaż")
        self._btn_toggle.setFixedWidth(80)
        self._btn_toggle.setMinimumHeight(32)
        self._btn_toggle.setCheckable(True)
        self._btn_toggle.toggled.connect(self._on_toggle_visibility)
        key_row.addWidget(self._btn_toggle)

        card_layout.addLayout(key_row)

        self._lbl_detected = QLabel("")
        self._lbl_detected.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        card_layout.addWidget(self._lbl_detected)

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

        instr_title = QLabel("Jak skonfigurować — przykład dla Google Gemini (darmowy)")
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
            "przycisk różdżki — kliknięcie wyśle obecną treść do AI i pokaże trzy warianty "
            "do wyboru: <b>korekta</b>, <b>formalny</b>, <b>przyjazny</b>.</p>"
        )
        steps.setWordWrap(True)
        steps.setOpenExternalLinks(True)
        steps.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; line-height: 1.5;")
        outer.addWidget(steps)

        providers_title = QLabel("Inni dostawcy LLM — możesz użyć dowolnego z tych kluczy")
        providers_title.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {COLORS['text']}; margin-top: 14px;"
        )
        outer.addWidget(providers_title)

        providers = QLabel(
            "<ul style='margin:0; padding-left: 20px;'>"
            f"<li><b>Google Gemini</b> — darmowy plan, ~1500 zapytań/dzień bez podawania karty. "
            f"Klucz: <a href='{AI_STUDIO_URL}' style='color:{COLORS['accent']};'>"
            f"aistudio.google.com/apikey</a></li>"
            f"<li><b>OpenAI</b> (GPT-4o-mini) — płatne, ale tanio (~$0,15 / 1 mln tokenów). "
            f"Klucz: <a href='{OPENAI_KEYS_URL}' style='color:{COLORS['accent']};'>"
            f"platform.openai.com/api-keys</a></li>"
            f"<li><b>Anthropic Claude</b> (Haiku 4.5) — płatne, bardzo dobre w polskim. "
            f"Klucz: <a href='{ANTHROPIC_KEYS_URL}' style='color:{COLORS['accent']};'>"
            f"console.anthropic.com</a></li>"
            "</ul>"
            "<p style='margin-top: 10px;'>Aplikacja rozpoznaje dostawcę automatycznie po formacie "
            "klucza (Gemini, <code>sk-</code> dla OpenAI, <code>sk-ant-</code> dla Anthropic). "
            "Wystarczy wkleić klucz i zapisać — nic więcej nie trzeba ustawiać.</p>"
            f"<p style='color:{COLORS['error']}; margin-top: 8px;'>⚠ <b>Prywatność:</b> "
            f"treść SMS-a wysyłana do AI trafia na serwery wybranego dostawcy. "
            f"<b>Nie wysyłaj danych wrażliwych</b> (PESEL, dane medyczne, hasła) — "
            f"używaj AI tylko do tekstów ogólnych (zaproszenia, powiadomienia, przypomnienia).</p>"
        )
        providers.setWordWrap(True)
        providers.setOpenExternalLinks(True)
        providers.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; line-height: 1.5;")
        outer.addWidget(providers)

        outer.addStretch()

    def _load_from_settings(self):
        self._input_key.setText(self._settings.gemini_api_key)
        self._chk_enabled.setChecked(self._settings.ai_enabled)
        self._on_key_changed(self._input_key.text())

    def _on_key_changed(self, text: str):
        key = (text or "").strip()
        if not key:
            self._lbl_detected.setText("")
            return
        provider = detect_provider(key)
        label = PROVIDER_LABELS.get(provider, provider)
        self._lbl_detected.setText(f"Wykryty dostawca: <b>{label}</b>")
        self._lbl_detected.setTextFormat(Qt.TextFormat.RichText)

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
