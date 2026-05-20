import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QWidget, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from gui.styles import COLORS


APP_VERSION = "2.0.1"

ABOUT_HTML = f"""
<div style="color: {COLORS['text']}; font-family: 'Segoe UI'; font-size: 13px; line-height: 1.55;">

<h2 style="color: {COLORS['accent']}; margin: 0 0 4px 0;">SMS Sender</h2>
<p style="color: {COLORS['text_secondary']}; margin: 0 0 18px 0;">Wersja {APP_VERSION}</p>

<h3 style="color: {COLORS['text']}; margin: 0 0 6px 0;">Właściciel aplikacji</h3>
<p style="margin: 0 0 18px 0;">
<b>Fundacja Full Steam Ahead</b>
</p>

<h3 style="color: {COLORS['text']}; margin: 0 0 6px 0;">Po co powstała ta aplikacja?</h3>
<p style="margin: 0 0 10px 0;">
Wierzymy, że organizacje pozarządowe w Polsce zasługują na profesjonalne narzędzia
tak samo jak korporacje &mdash; tylko bez korporacyjnych kosztów.
</p>
<p style="margin: 0 0 10px 0;">
SMS Sender powstał, żeby pomóc fundacjom, stowarzyszeniom, klubom i małym
inicjatywom szybciej docierać do swoich odbiorców. Bez bramek SMS, bez
abonamentów, bez kombinowania. Wystarczy Twój telefon i lista numerów.
</p>
<p style="margin: 0 0 18px 0;">
<b>Oddajemy SMS Sender całkowicie bezpłatnie w Wasze ręce.</b>
To nasz wkład w to, żeby III sektor w Polsce mógł działać sprawniej, a Wy
mogliście skupić się na tym, co naprawdę ważne &mdash; na zmienianiu świata.
</p>

<h3 style="color: {COLORS['text']}; margin: 0 0 6px 0;">Jak działa aplikacja?</h3>
<p style="margin: 0 0 8px 0;">
SMS Sender automatyzuje wysyłkę wiadomości przez wbudowaną w Windows aplikację
<b>Łącze z telefonem</b> (Phone Link) i Twój prywatny telefon z Androidem.
Każdy SMS wysyłany jest z Twojego numeru, zgodnie z Twoim abonamentem operatora.
</p>
<p style="margin: 0 0 6px 0;"><b>Wymagania:</b></p>
<ul style="margin: 0 0 10px 18px; padding: 0;">
<li>Windows 10 lub Windows 11</li>
<li>Telefon z Androidem i aplikacją <b>Link do Windows</b></li>
<li>Aplikacja <b>Łącze z telefonem</b> (wbudowana w Windows, dostępna też w Microsoft Store)</li>
</ul>
<p style="margin: 0 0 6px 0;"><b>Przed pierwszym użyciem &mdash; krok po kroku:</b></p>
<ol style="margin: 0 0 10px 18px; padding: 0;">
<li>Otwórz <b>Łącze z telefonem</b> na komputerze</li>
<li>Sparuj telefon: zeskanuj kod QR aplikacją <b>Link do Windows</b> na Androidzie</li>
<li>W Łączu z telefonem wejdź w zakładkę <b>Wiadomości</b></li>
<li>Wyślij testowy SMS do siebie &mdash; musi zadziałać</li>
<li>Dopiero wtedy uruchom SMS Sender</li>
</ol>
<p style="margin: 0 0 8px 0;"><b>Jak korzystać z SMS Sender:</b></p>
<ol style="margin: 0 0 18px 18px; padding: 0;">
<li>Zaimportuj listę odbiorców z pliku Excel / CSV lub wklej numery (Ctrl+V)</li>
<li>Napisz treść wiadomości (możesz użyć zmiennych: {{"{{"}}Imie{{"}}"}}, {{"{{"}}Firma{{"}}"}} itp.)</li>
<li>Sprawdź podgląd &mdash; odznacz osoby, do których nie chcesz wysyłać</li>
<li>Kliknij <b>Wyślij SMS</b> i nie dotykaj myszy &mdash; aplikacja robi resztę</li>
</ol>
<p style="margin: 0 0 18px 0; color: {COLORS['text_secondary']};">
<b>Uwaga:</b> aplikacja działa wyłącznie na systemie <b>Windows</b>.
Okno Łącza z telefonem musi być otwarte i widoczne podczas wysyłki (nie zminimalizowane).
</p>

<h3 style="color: {COLORS['text']}; margin: 0 0 6px 0;">Licencja</h3>
<p style="margin: 0 0 10px 0;">
Aplikacja udostępniana jest na licencji <b>MIT</b> &mdash; możesz jej używać,
kopiować, modyfikować i rozpowszechniać swobodnie, w tym w celach komercyjnych.
</p>
<p style="margin: 0 0 18px 0;">
Pełny tekst licencji znajdziesz w pliku <code>LICENSE</code> w folderze instalacji.
</p>

<h3 style="color: {COLORS['text']}; margin: 0 0 6px 0;">Prywatność</h3>
<p style="margin: 0 0 18px 0;">
Aplikacja <b>nie wysyła żadnych danych na zewnątrz</b>. Cała wysyłka SMS-ów
odbywa się lokalnie &mdash; przez Łącze z telefonem i Twój prywatny telefon.
Numery odbiorców i treści wiadomości nigdy nie opuszczają Twojego komputera.
</p>

<h3 style="color: {COLORS['text']}; margin: 0 0 6px 0;">Podziękowania</h3>
<p style="margin: 0 0 8px 0;">
Aplikacja zbudowana w oparciu o świetne biblioteki open source:
</p>
<ul style="margin: 0 0 18px 18px; padding: 0;">
<li>PySide6 (Qt) &mdash; interfejs graficzny</li>
<li>pywinauto &mdash; automatyzacja Windows</li>
<li>openpyxl &mdash; obsługa plików Excel</li>
<li>phonenumbers &mdash; walidacja numerów</li>
</ul>

<p style="color: {COLORS['text_secondary']}; margin: 16px 0 0 0; font-size: 12px;">
Jeśli SMS Sender pomógł Twojej organizacji &mdash; daj nam znać.
To dla nas największa nagroda.<br>
Kontakt: <a href="mailto:kontakt@fullsteam.pl" style="color: {COLORS['accent']};">kontakt@fullsteam.pl</a>
</p>

</div>
"""


class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QScrollArea {{ background-color: {COLORS['surface']}; border: none; }}
            QScrollArea > QWidget > QWidget {{ background-color: {COLORS['surface']}; }}
            QLabel {{ background-color: transparent; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 20, 32, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(14)

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resources", "icon.png"
        )
        if os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path).scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_label.setPixmap(pixmap)
            header.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("SMS Sender")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: 600; color: {COLORS['text']};"
        )
        subtitle = QLabel("Bezpłatne narzędzie do masowej wysyłki SMS")
        subtitle.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px;"
        )
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)

        layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        body = QLabel(ABOUT_HTML)
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setWordWrap(True)
        body.setOpenExternalLinks(True)
        body.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        content_layout.addWidget(body)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
