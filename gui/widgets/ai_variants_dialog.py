from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QFrame, QTextEdit,
)
from PySide6.QtCore import Qt

from gui.styles import COLORS


VARIANT_LABELS = {
    "korekta": ("Korekta", "Minimalna poprawa: gramatyka, interpunkcja, polskie znaki."),
    "formalny": ("Formalny", "Urzędowy, profesjonalny ton."),
    "przyjazny": ("Przyjazny", "Ciepły, ludzki, naturalny ton."),
}


class AIVariantsDialog(QDialog):
    """Modal showing three AI-generated SMS variants for the user to pick."""

    def __init__(self, original: str, variants: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wybierz wariant — Asystent AI")
        self.setModal(True)
        self.resize(620, 480)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg']}; }}")

        self._variants = variants
        self._selected_key = "korekta"
        self._radios = {}
        self._previews = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(12)

        header = QLabel("Trzy propozycje od asystenta AI")
        header.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {COLORS['text']};"
        )
        outer.addWidget(header)

        if original:
            orig_card = QFrame()
            orig_card.setStyleSheet(
                f"QFrame {{ background-color: {COLORS['hover']}; "
                f"border: 1px solid {COLORS['border']}; border-radius: 6px; }}"
            )
            ol = QVBoxLayout(orig_card)
            ol.setContentsMargins(12, 8, 12, 8)
            ol.setSpacing(4)
            lbl_orig_title = QLabel("Twój oryginał")
            lbl_orig_title.setStyleSheet(
                f"font-size: 11px; font-weight: 600; color: {COLORS['text_secondary']};"
                f" text-transform: uppercase; letter-spacing: 0.5px;"
            )
            ol.addWidget(lbl_orig_title)
            lbl_orig = QLabel(original)
            lbl_orig.setWordWrap(True)
            lbl_orig.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px;")
            ol.addWidget(lbl_orig)
            outer.addWidget(orig_card)

        self._group = QButtonGroup(self)

        for key in ("korekta", "formalny", "przyjazny"):
            if key not in variants:
                continue
            title, desc = VARIANT_LABELS[key]
            card = self._build_variant_card(key, title, desc, variants[key])
            outer.addWidget(card)

        if self._radios:
            first_key = next(iter(self._radios))
            self._radios[first_key].setChecked(True)
            self._selected_key = first_key

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Anuluj")
        btn_cancel.setMinimumWidth(110)
        btn_cancel.setMinimumHeight(34)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_use = QPushButton("Użyj wybranego wariantu")
        btn_use.setProperty("class", "primary")
        btn_use.setMinimumWidth(200)
        btn_use.setMinimumHeight(34)
        btn_use.setDefault(True)
        btn_use.clicked.connect(self.accept)
        btn_row.addWidget(btn_use)

        outer.addLayout(btn_row)

    def _build_variant_card(self, key: str, title: str, desc: str, text: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['surface']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
            f"QFrame:hover {{ border-color: {COLORS['accent']}; }}"
        )

        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 10, 14, 12)
        cl.setSpacing(6)

        head_row = QHBoxLayout()
        head_row.setSpacing(8)

        radio = QRadioButton(title)
        radio.setStyleSheet(
            f"QRadioButton {{ font-weight: 600; font-size: 13px; color: {COLORS['text']}; }}"
        )
        radio.toggled.connect(lambda checked, k=key: self._on_variant_selected(k, checked))
        self._group.addButton(radio)
        self._radios[key] = radio
        head_row.addWidget(radio)

        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        head_row.addWidget(lbl_desc)
        head_row.addStretch()

        char_count = QLabel(f"{len(text)} znaków")
        char_count.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
        head_row.addWidget(char_count)

        cl.addLayout(head_row)

        preview = QTextEdit()
        preview.setPlainText(text)
        preview.setReadOnly(True)
        preview.setMaximumHeight(80)
        preview.setStyleSheet(
            f"QTextEdit {{ background-color: {COLORS['input_bg']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 6px; "
            f"padding: 6px; font-size: 12px; color: {COLORS['text']}; }}"
        )
        cl.addWidget(preview)
        self._previews[key] = preview

        card.mousePressEvent = lambda e, k=key: self._radios[k].setChecked(True)
        return card

    def _on_variant_selected(self, key: str, checked: bool):
        if checked:
            self._selected_key = key

    def selected_text(self) -> str:
        return self._variants.get(self._selected_key, "")
