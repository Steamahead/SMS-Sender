# SMS Sender v2 — Design Spec

## Cel
Rozbudowa SMS Sender o nowe funkcjonalnosci, pelna przebudowa UI na PySide6, oraz przygotowanie instalki do dystrybucji organizacjom.

## Zakres zmian

### 1. Import numerow — rozbudowa

#### 1.1 Auto-detekcja kolumny
- Przy imporcie Excel/CSV aplikacja skanuje **wszystkie kolumny** w pierwszych 50 wierszach
- Dla kazdej kolumny liczy ile wartosci przechodzi walidacje `phonenumbers` jako numer PL
- Kolumna z najwieksza liczba trafien zostaje wybrana automatycznie
- W GUI pojawia sie **dropdown** z lista kolumn (A, B, C...) — uzytkownik moze zmienic wybor
- Po zmianie kolumny lista numerow odswieza sie natychmiast

#### 1.2 Drag & drop pliku
- Uzytkownik moze przeciagnac plik `.xlsx` lub `.csv` na okno aplikacji
- Plik zostaje zaimportowany tak samo jak przez przycisk "Importuj"
- Wizualny feedback: strefa drop podswietla sie przy przeciaganiu pliku nad oknem
- Implementacja: QDragEnterEvent + QDropEvent w PySide6 (natywne wsparcie)

#### 1.3 Ctrl+V ze schowka
- Uzytkownik zaznacza komorki w Excelu, kopiuje (Ctrl+C), przechodzi do aplikacji i wkleja (Ctrl+V)
- Aplikacja parsuje schowek jako tekst tab-separated (format Excela)
- Kazda linia traktowana jako potencjalny numer — przechodzi przez normalize + validate
- Numery dodawane do istniejącej listy (nie zastepuja)
- Jesli schowek nie zawiera zadnych prawidlowych numerow — komunikat bledu

#### 1.4 Oczyszczanie numerow (juz zaimplementowane)
- Strip: spacje (leading, trailing, wewnetrzne), myslniki, nawiasy `()`, kropki `.`
- Normalizacja do formatu E164 (`+48XXXXXXXXX`)
- Nie ingeruje w cyfry — tylko usuwa formatowanie

### 2. Personalizacja wiadomosci

#### 2.1 Zmienne w tresci
- Uzytkownik moze uzyc zmiennych w tresci SMS: `{imie}`, `{firma}`, `{kolumna_X}`
- Zmienne mapowane na kolumny z zaimportowanego pliku Excel/CSV
- W GUI: dropdown lub autocomplete z dostepnymi kolumnami po zaimportowaniu pliku
- Walidacja: jesli zmienna nie ma odpowiednika w danych — ostrzezenie przed wysylka

#### 2.2 Mapowanie kolumn
- Po imporcie pliku aplikacja wykrywa naglowki kolumn (pierwszy wiersz)
- Uzytkownik moze uzyc nazw kolumn jako zmiennych: `{Imie}`, `{Nazwisko}`, `{Firma}`
- Jesli brak naglowkow — zmienne po literach: `{A}`, `{B}`, `{C}`

### 3. Podglad przed wysylka

- Tabela w GUI: **Numer | Tresc (z podstawionymi zmiennymi) | Status**
- Uzytkownik widzi dokladnie co pojdzie do kazdego odbiorcy
- Mozliwosc odznaczenia pojedynczych odbiorcow (checkbox)
- Status aktualizowany w trakcie wysylki: Oczekuje → Wysylanie → Wyslano / Blad

### 4. Szablony wiadomosci

- Zapisywanie tresci SMS jako szablon z nazwa
- Lista zapisanych szablonow — klik laduje tresc do pola wiadomosci
- Szablony przechowywane w pliku JSON w katalogu uzytkownika (`%APPDATA%/SMSSender/templates.json`)
- Operacje: Zapisz jako szablon / Zaladuj szablon / Usun szablon
- Szablony moga zawierac zmienne (`{imie}` itd.)

### 5. Historia wysylki

- Kazda sesja wysylki zapisywana z:
  - Data i godzina
  - Lista odbiorcow z statusami (wyslano/blad/pominieto)
  - Tresc wiadomosci
  - Nazwa pliku zrodlowego
- Przechowywanie: SQLite w `%APPDATA%/SMSSender/history.db`
- W GUI: zakladka "Historia" z lista sesji, klik otwiera szczegoly
- Przechowywanie ostatnich 1000 sesji (stare automatycznie usuwane)

### 6. Raport po wysylce

#### 6.1 Raport w GUI
- Po zakonczeniu wysylki — podsumowanie:
  - Wyslano: X
  - Bledy: Y
  - Pominieto: Z
- Lista blednych numerow z przyczyna bledu

#### 6.2 Eksport raportu
- Przycisk "Eksportuj raport" — zapis do Excel (.xlsx) lub CSV
- Kolumny: Numer | Status | Tresc | Czas wyslania | Blad (jesli byl)
- Domyslna nazwa: `raport_SMS_YYYY-MM-DD_HHMMSS.xlsx`

### 7. Deduplikacja numerow

- Przy imporcie: automatyczne wykrywanie duplikatow po normalizacji
- Komunikat: "Znaleziono X duplikatow — usunieto"
- Duplikaty usuwane po cichu (nie blokuja importu)
- Dotyczy rowniez dodawania recznego i Ctrl+V — nie pozwala dodac numeru ktory juz jest na liscie

### 8. Licznik SMS

- Wyswietlanie przy polu tresci: `Znaki: 45/160 (1 SMS)` lub `Znaki: 200/320 (2 SMS-y)`
- Progi: 160 znaków = 1 SMS, 306 znakow = 2 SMS-y (GSM 7-bit)
- Informacja ile SMS-ow lacznie zostanie wyslanych: `Odbiorcy: 50 × 2 SMS = 100 SMS-ow`
- Limit tresci: 320 znakow (jak obecnie)

### 9. Zapamiętywanie ustawien

- Plik konfiguracji: `%APPDATA%/SMSSender/settings.json`
- Zapisywane:
  - Ostatnio uzywany folder importu
  - Rozmiar i pozycja okna
  - Rozmiar paczki (domyslnie 20)
  - Ostatnio uzywany szablon

## Architektura

### Struktura modulow (po zmianach)

```
sms-sender/
├── main.py                    # Entry point
├── core/
│   ├── excel_importer.py      # Import + auto-detekcja kolumny + oczyszczanie
│   ├── batch_manager.py       # Paczki, status tracking
│   ├── sender.py              # ABC + PhoneLinkSender wrapper
│   ├── template_manager.py    # NOWY: zapis/odczyt szablonow (JSON)
│   ├── history.py             # NOWY: historia wysylki (SQLite)
│   ├── report.py              # NOWY: generowanie raportow (Excel/CSV)
│   ├── settings.py            # NOWY: persystencja ustawien
│   └── personalizer.py        # NOWY: podstawianie zmiennych w tresci
├── automation/
│   └── phone_link.py          # pywinauto UIA (bez zmian)
├── gui/
│   ├── app.py                 # PRZEPISANY: PySide6 glowne okno
│   ├── widgets/               # NOWY: komponenty UI
│   │   ├── import_panel.py    # Panel importu (drag&drop, ctrl+v, dropdown kolumn)
│   │   ├── message_panel.py   # Panel tresci (edytor, zmienne, licznik)
│   │   ├── preview_table.py   # Tabela podgladu odbiorcow
│   │   ├── send_panel.py      # Panel wysylki (progress, log, stop/resume)
│   │   ├── history_view.py    # Widok historii
│   │   └── template_dialog.py # Dialog szablonow
│   ├── styles.py              # NOWY: QSS stylesheet, paleta kolorow
│   └── resources/             # NOWY: ikony, fonty
├── installer/
│   ├── sms_sender.iss         # NOWY: Inno Setup script
│   ├── icon.ico               # NOWY: ikona aplikacji
│   └── build.py               # NOWY: skrypt budowania (PyInstaller + Inno Setup)
├── tests/
├── tools/
└── docs/
```

### Przepływ danych

```
Excel/CSV/Clipboard
        │
        ▼
  ExcelImporter (auto-detect column, normalize, validate, deduplicate)
        │
        ▼
  Personalizer (parse template variables, map to columns)
        │
        ▼
  PreviewTable (show each recipient + personalized message)
        │
        ▼
  BatchManager (split into batches of 20)
        │
        ▼
  PhoneLinkSender (pywinauto UIA → Phone Link)
        │
        ▼
  History + Report (save results, enable export)
```

### UI Layout (PySide6)

```
┌─────────────────────────────────────────────────┐
│  SMS Sender                              [─][□][×]│
├─────────────────────────────────────────────────┤
│  [Wysylka]  [Historia]                          │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─ Import ──────────────────────────────────┐  │
│  │  [Importuj plik]  Kolumna: [▼ A (auto)]   │  │
│  │  📎 Przeciagnij plik tutaj lub Ctrl+V      │  │
│  │  Zaladowano: 50 numerow (2 duplikaty       │  │
│  │  usuniete, 3 pominiete)                    │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌─ Tresc SMS ───────────────────────────────┐  │
│  │  [▼ Szablony]  [Zapisz szablon]           │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │ Witaj {Imie}, przypominamy o...     │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │  Znaki: 45/160 (1 SMS) │ 50 × 1 = 50 SMS │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌─ Podglad odbiorcow ──────────────────────┐  │
│  │  ☑ +48512345678  │ Witaj Jan, przyp...   │  │
│  │  ☑ +48698765432  │ Witaj Anna, przyp...  │  │
│  │  ☐ +48111222333  │ Witaj {Imie}, przy... │  │
│  │                   (brak danych dla Imie)  │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  [▶ Wyslij]  [⏹ Stop]  [↻ Wznow]              │
│  ████████████████░░░░░░  Paczka 3/5            │
│                                                 │
│  ┌─ Log ─────────────────────────────────────┐  │
│  │ 14:32:01 Wysylam SMS 1/50: +48512345678   │  │
│  │ 14:32:05 Wyslano                          │  │
│  │ 14:32:06 Wysylam SMS 2/50: +48698765432   │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  [Eksportuj raport]                             │
└─────────────────────────────────────────────────┘
```

### Styl wizualny

- **Framework**: PySide6 z QSS (Qt Style Sheets)
- **Styl**: Nowoczesny/startup
  - Zaokraglone rogi (border-radius: 8-12px)
  - Gradientowe akcenty na przyciskach (np. niebieski → ciemniejszy niebieski)
  - Duzo bialej przestrzeni (padding, margin)
  - Cienie (drop-shadow) na panelach
  - Font: Segoe UI lub Inter
- **Paleta kolorow**:
  - Tlo: #FAFBFC (jasny szary)
  - Panele: #FFFFFF z cieniem
  - Akcent glowny: #2563EB (niebieski) z gradientem do #1D4ED8
  - Akcent sukcesu: #16A34A (zielony)
  - Akcent bledu: #DC2626 (czerwony)
  - Tekst glowny: #1F2937
  - Tekst drugorzedny: #6B7280
- **Ikony**: Wbudowane Qt icons lub zestaw SVG (Lucide/Feather icons)

### Dystrybucja

#### PyInstaller
- Budowanie do jednego katalogu (nie `--onefile` — szybsze uruchamianie)
- Wlaczenie PySide6, openpyxl, pywinauto, phonenumbers
- Ikona aplikacji: `installer/icon.ico`
- Ukrycie konsoli: `--windowed`

#### Inno Setup
- Installer `.exe` z:
  - Ekran powitalny z logo
  - Wybor katalogu instalacji (domyslnie `C:\Program Files\SMS Sender`)
  - Tworzenie skrotu na pulpicie
  - Tworzenie wpisu w "Dodaj/Usun programy"
  - Opcja uruchomienia po instalacji
- Deinstalator (standardowy Inno Setup uninstaller)

## Migracja z tkinter na PySide6

1. `gui/app.py` — przepisanie od zera (PySide6 QMainWindow)
2. Wydzielenie widgetow do `gui/widgets/`
3. Style w osobnym pliku `gui/styles.py` (QSS)
4. `main.py` — zmiana z `tk.Tk()` na `QApplication`
5. Modul `automation/phone_link.py` — bez zmian
6. Modul `core/` — rozbudowa, nie przepisywanie

## Testy

- Istniejace testy `test_excel_importer.py`, `test_batch_manager.py`, `test_sender.py` — adaptacja
- Nowe testy:
  - `test_personalizer.py` — podstawianie zmiennych, brakujace dane
  - `test_template_manager.py` — zapis/odczyt/usuwanie szablonow
  - `test_history.py` — zapis/odczyt sesji, limit 1000
  - `test_report.py` — eksport do Excel/CSV
  - `test_settings.py` — persystencja ustawien
  - `test_column_detection.py` — auto-detekcja kolumny z numerami
  - `test_deduplication.py` — wykrywanie duplikatow
  - `test_clipboard_import.py` — parsowanie schowka

## Znane ograniczenia

- Phone Link wymaga fokusu okna — komputer zablokowany podczas wysylki
- pywinauto UIA — selektory moga sie zmieniac miedzy wersjami Phone Link
- Brak potwierdzenia dostarczenia SMS (Phone Link nie udostepnia statusu delivery)
