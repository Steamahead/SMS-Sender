# SMS Sender — Design Spec

## Cel

Aplikacja desktopowa do wysyłania SMS-ów z komputera przez Windows Phone Link. Numery telefonów importowane z Excela, wysyłka w paczkach po max 20 odbiorców. Darmowe rozwiązanie — bez zewnętrznych API, SMS-y wychodzą z prywatnego numeru użytkownika (Android).

## Architektura

```
┌─────────────────────────────────────┐
│           GUI (tkinter)             │
│  ┌───────────┐  ┌────────────────┐  │
│  │ Excel     │  │ Composer       │  │
│  │ Import    │  │ (treść SMS +   │  │
│  │ Panel     │  │  podgląd paczek│  │
│  └─────┬─────┘  └───────┬────────┘  │
│        └────────┬────────┘          │
│                 ▼                    │
│        BatchManager                 │
│    (dzieli numery na paczki ≤20)    │
│                 │                    │
│                 ▼                    │
│        SMSSender (interfejs)        │
│           │                         │
│           ▼                         │
│     PhoneLinkSender                 │
│    (PyAutoGUI automation)           │
└─────────────────────────────────────┘
```

### Moduły

1. **ExcelImporter** — wczytuje `.xlsx`/`.csv`, waliduje numery (format PL przez bibliotekę `phonenumbers`), zwraca listę prawidłowych numerów + listę odrzuconych z powodem
2. **BatchManager** — dzieli listę na paczki po max 20, śledzi status każdej paczki (oczekująca / wysłana / błąd), umożliwia wznowienie od ostatniej niewysłanej paczki
3. **SMSSender (interfejs)** — abstrakcja z metodą `send(numbers, message)`. Implementacja: `PhoneLinkSender`. Architektura pozwala na dodanie `AdbSender` w przyszłości bez zmiany reszty kodu
4. **PhoneLinkSender** — automatyzacja Phone Link przez PyAutoGUI (image recognition)
5. **GUI (app.py)** — tkinter, jeden ekran z importem, edycją treści, podglądem paczek, progress barem i logiem

## Workflow użytkownika

1. Otwiera aplikację
2. Klika "Importuj Excel" → wybiera plik → widzi listę numerów z walidacją (✓/✗)
3. Wpisuje treść SMS-a (licznik znaków, limit 160)
4. Widzi podgląd paczek (np. "4 × 20 = 80 numerów")
5. Klika "Wyślij"
6. Aplikacja automatyzuje Phone Link — dla każdej paczki:
   a. Otwiera nową wiadomość
   b. Dodaje numery (max 20) — wpisuje każdy w pole "Do:" + Enter
   c. Wkleja treść (Ctrl+V dla polskich znaków)
   d. Klika Wyślij
   e. Pauza 3-5 sekund → następna paczka
7. Progress bar + log na żywo
8. Podsumowanie: wysłane / pominięte / błędy

## Phone Link Automation — sekwencja

Metoda: **Image Recognition** (`PyAutoGUI.locateOnScreen`) — szuka elementów wizualnie na screenshotach referencyjnych zamiast hardkodowanych koordynatów.

```
1. Fokus na okno Phone Link (pywinauto — znajdź po tytule okna)
2. Kliknij "Wiadomości" (jeśli nie jest już otwarte)
3. Kliknij "Nowa wiadomość" (ikona +)
4. Dla każdego numeru w paczce (max 20):
   a. Kliknij pole "Do:"
   b. Wpisz numer (pyautogui.typewrite)
   c. Potwierdź Enter (dodaje odbiorcę)
   d. Czekaj 0.5s
5. Kliknij pole treści wiadomości
6. Wklej treść (Ctrl+V)
7. Kliknij Wyślij
8. Czekaj 3-5s → następna paczka
```

### Kalibracja

Dostarczamy gotowe screenshoty referencyjne z domyślnej instalacji Phone Link. Jeśli nie pasują — tryb kalibracji, w którym użytkownik wskazuje elementy ręcznie.

### Zabezpieczenia

- Przed każdą akcją sprawdzamy czy Phone Link jest na wierzchu
- Timeout 10s na znalezienie każdego elementu — jeśli nie znajdzie → stop
- Użytkownik nie powinien ruszać myszką podczas wysyłki

## Obsługa błędów

| Błąd | Reakcja |
|------|---------|
| Phone Link nie otwarty / nie znaleziono okna | Próba uruchomienia automatycznie. Jeśli się nie uda → stop + komunikat "Otwórz Phone Link i połącz telefon, potem kliknij Wznów" |
| Telefon niepołączony | Czeka 15s, retry raz. Jeśli dalej nie działa → stop + komunikat |
| Element UI nie znaleziony (image recognition fail) | Stop + komunikat "Nie mogę znaleźć elementu X. Sprawdź czy okno jest widoczne" |
| Nieprawidłowy numer telefonu | Wykrywany przy imporcie. Trafia na listę "Pominięte" z powodem |
| Wysyłka paczki nie powiodła się | Zapisuje stan (które paczki wysłane). Przycisk "Wznów" kontynuuje od ostatniej niewysłanej |
| Błąd odczytu Excela | Komunikat przy imporcie: "Wiersz X: problem, pomijam" |

**Zasada:** Błędy przed wysyłką → napraw i spróbuj ponownie. Błędy w trakcie → stop + wznów od miejsca przerwania. Po zakończeniu → raport.

## GUI — układ okna

```
┌──────────────────────────────────────────────┐
│  SMS Sender                            [—][×]│
├──────────────────────────────────────────────┤
│                                              │
│  [Importuj Excel]  plik: kontakty.xlsx       │
│  Załadowano: 73 numery (2 pominięte)         │
│                                              │
│  ┌─ Numery ──────────────────────────────┐   │
│  │ +48 512 345 678                    ✓  │   │
│  │ +48 601 234 567                    ✓  │   │
│  │ +48 abc def ghi                    ✗  │   │
│  │ ...                                   │   │
│  └───────────────────────────────────────┘   │
│                                              │
│  Treść SMS:                                  │
│  ┌───────────────────────────────────────┐   │
│  │ Przypominamy o spotkaniu w piątek...  │   │
│  └───────────────────────────────────────┘   │
│  Znaki: 42/160                               │
│                                              │
│  Paczki: 4 × 20 = 80 numerów                │
│                                              │
│  [ ▶ Wyślij ]  [ ⏹ Stop ]  [ ↻ Wznów ]     │
│                                              │
│  ████████░░░░░░░░  Paczka 2/4                │
│                                              │
│  Log:                                        │
│  12:01 Paczka 1/4 wysłana (20 numerów)       │
│  12:01 Paczka 2/4 w trakcie...               │
│                                              │
└──────────────────────────────────────────────┘
```

## Struktura plików

```
sms-sender/
├── main.py                  # Entry point — uruchamia GUI
├── gui/
│   └── app.py               # Okno tkinter, cały layout
├── core/
│   ├── excel_importer.py    # Wczytywanie Excel/CSV, walidacja numerów
│   ├── batch_manager.py     # Dzielenie na paczki ≤20, śledzenie statusu
│   └── sender.py            # SMSSender interfejs + PhoneLinkSender
├── automation/
│   └── phone_link.py        # PyAutoGUI logika — sekwencja kliknięć
├── assets/
│   └── screenshots/         # Referencyjne screenshoty elementów Phone Link
├── requirements.txt         # openpyxl, pyautogui, pywinauto, phonenumbers
└── README.md
```

## Technologie

- Python 3.12+
- tkinter (GUI — wbudowane w Python)
- openpyxl (odczyt Excel .xlsx)
- PyAutoGUI (automatyzacja — kliknięcia, wpisywanie, image recognition)
- pywinauto (zarządzanie oknami Windows — fokus, znajdowanie po tytule)
- phonenumbers (walidacja numerów PL)

## Przyszła rozbudowa

Architektura z interfejsem `SMSSender` pozwala na dodanie `AdbSender` (Podejście 3) bez zmiany reszty aplikacji. Wymaga tylko nowej klasy implementującej `send(numbers, message)`.

## Ograniczenia

- Wymaga otwartego Phone Link z połączonym telefonem Android
- Użytkownik nie może ruszać myszką podczas wysyłki
- Zależność od UI Phone Link — zmiana layoutu może wymagać nowych screenshotów referencyjnych
- Max 20 odbiorców na paczkę (limit Phone Link)
- Polskie numery — walidacja domyślnie dla PL. Akceptuje formaty: `+48512345678`, `48512345678`, `512345678`. Wszystkie normalizowane do formatu `+48XXXXXXXXX` przed wysyłką
