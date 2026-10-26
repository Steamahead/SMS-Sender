# SMS Sender v2 — Status

## Aktualny stan: 2.3.1 — wydane, test wysylki do siebie potwierdzony

Release: https://github.com/Steamahead/SMS-Sender/releases/tag/2.3.1 (Latest)

## Zrealizowane funkcjonalnosci

**Odbiorcy i tresc**
- Import numerow: Excel/CSV z auto-detekcja kolumny, drag & drop, Ctrl+V ze schowka
- CSV z polskiego Excela (srednik, cp1250 / UTF-8 z BOM) — `read_csv_rows`
- Kilka numerow w jednej komorce (przecinek, srednik, Alt+Enter) — wklejanie i import
- Reczne wpisywanie numerow telefonu (pole + przycisk Dodaj)
- Deduplikacja numerow
- Personalizacja wiadomosci: zmienne {Imie}, {Firma} mapowane na kolumny —
  od wersji roboczej po 2.2.2 faktycznie trafia do odbiorcow (wczesniej tylko
  podglad); ostrzezenie o literowce w zmiennej ({imie} → {Imię}?)
- Szablony SMS: zapis/odczyt/edycja/usuwanie (JSON)
- Licznik SMS liczy prawdziwe czesci (GSM-7 160/153, UCS-2 70/67), limit 700 znakow
- Przelacznik "Bez polskich znakow" (~2x mniej czesci), "Wyslij test do siebie",
  potwierdzenie wysylki z liczba czesci i ostrzezeniami (zmienne, MMS)
- Rozciagane panele (QSplitter) na Wysylce i w Historii, uklad zapamietywany
- Uchwyt w rogu kazdego pola tekstowego (`gui/widgets/resize_grip.py`): w oknie
  glownym powieksza panel kosztem sasiadow, w dialogach zmienia rozmiar okna
- Reczne pole numeru przyjmuje kilka numerow po przecinku/sredniku
- Podglad odbiorcow: tabela z checkboxami, zaznacz/odznacz wszystkie,
  usuwanie pojedynczego numeru, stan checkboxow przezywa edycje wiadomosci

**Asystent AI (2.1.x)**
- `core/ai_refine.py` — multi-provider (Gemini/OpenAI/Anthropic), auto-detekcja
  po prefiksie klucza, stdlib only (urllib + json)
- Dialog 3 wariantow: korekta / formalny / przyjazny
- Tab "Ustawienia" z polem klucza i wskaznikiem wykrytego dostawcy

**Wysylka**
- Paczki po 20 numerow, losowa przerwa 4–8 s miedzy paczkami
- Wynik liczony **per odbiorca**, nie per paczka (2.2.2)
- Jeden nieudany numer nie przerywa wysylki reszty listy
- "Wznow" ponawia wylacznie numery, ktore sie nie udaly
- Weryfikacja numeru i tresci **przed** wyslaniem — ponowienie nigdy nie
  duplikuje SMS-a, ktory juz poszedl

**Dane i bezpieczenstwo**
- Historia wysylki: SQLite, max 1000 sesji, retencja 90 dni (RODO),
  usuwanie pojedynczej sesji i calej historii
- Klucz API szyfrowany Windows DPAPI (`core/crypto_store.py`)
- Raport po wysylce: eksport XLSX/CSV z ochrona przed formula injection
- Zapamietywanie ustawien (JSON)

**UI**
- Polskie znaki w calym interfejsie, poprawna odmiana liczebnikow
  (1 numer, 2 numery, 5 numerow)
- Ikona aplikacji (dymek SMS)

## Build

```
python installer/build.py                                    # dist/SMSSender/SMSSender.exe
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\sms_sender.iss
```
Output instalatora: `dist/installer/SMSSender_Setup_X.Y.Z.exe`

Bump wersji zawsze w 3 miejscach: `gui/widgets/about_dialog.py`,
`installer/sms_sender.iss`, `README.md`.

Release: `gh release create X.Y.Z dist/installer/SMSSender_Setup_X.Y.Z.exe --title "SMS Sender X.Y.Z" --notes-file docs/release-notes-X.Y.Z.md --latest`
(`gh` jest zalogowany z keyringa — web UI nie jest potrzebne).

## Testy: 175 PASS

```
pytest tests/ -q
```

## Zmiany w automation/phone_link.py — najpierw zmierz

Testy jednostkowe nie wystarczaja; patrz `CLAUDE.md`. Przed zmiana:

```
python tools/diagnose_compose.py <prawdziwy_numer>   # zrzut drzewa UIA po kazdym kroku
python tools/dryrun_send.py <numer> 3                # caly flow bez wysylki
```

Podaj numer z **istniejaca konwersacja** — numer bez niej idzie inna sciezka
przez Phone Link i nie odtworzy problemu.

## Nastepne kroki
- Dystrybucja: ngo.pl, Sektor 3.0/TechSoup, grupy FB NGO, dobreprogramy.pl
- Wysylka na wiekszej liscie (ostatnia potwierdzona: 69 osob na 2.2.0)
