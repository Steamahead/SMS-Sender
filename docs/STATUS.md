# SMS Sender v2 — Status

## Aktualny stan: 2.2.2 — wydane, zweryfikowane realna wysylka

Release: https://github.com/Steamahead/SMS-Sender/releases/tag/2.2.2 (Latest)

## Zrealizowane funkcjonalnosci

**Odbiorcy i tresc**
- Import numerow: Excel/CSV z auto-detekcja kolumny, drag & drop, Ctrl+V ze schowka
- Reczne wpisywanie numerow telefonu (pole + przycisk Dodaj)
- Deduplikacja numerow
- Personalizacja wiadomosci: zmienne {Imie}, {Firma} mapowane na kolumny
- Szablony SMS: zapis/odczyt/edycja/usuwanie (JSON)
- Licznik SMS (znaki + ilosc SMS-ow), limit 500 znakow
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

## Testy: 128 PASS

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
