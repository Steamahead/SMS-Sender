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
│    (pywinauto UIA automation)       │
└─────────────────────────────────────┘
```

### Moduły

1. **ExcelImporter** — wczytuje `.xlsx`/`.csv`, waliduje numery (format PL przez bibliotekę `phonenumbers`), zwraca listę prawidłowych numerów + listę odrzuconych z powodem
2. **BatchManager** — dzieli listę na paczki po max 20, śledzi status każdej paczki (oczekująca / wysłana / błąd), umożliwia wznowienie od ostatniej niewysłanej paczki
3. **SMSSender (interfejs)** — abstrakcja z metodą `send(numbers, message)`. Implementacja: `PhoneLinkSender`. Architektura pozwala na dodanie `AdbSender` w przyszłości bez zmiany reszty kodu
4. **PhoneLinkSender** — automatyzacja Phone Link przez pywinauto UIA (UI Automation — znajduje kontrolki po nazwie i typie, odporne na skalowanie/motywy/rozdzielczości)
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
   e. Losowa pauza 4-8 sekund → następna paczka
7. Progress bar + log na żywo
8. Podsumowanie: wysłane / pominięte / błędy

## Phone Link Automation — sekwencja

Metoda: **pywinauto UIA (UI Automation)** — znajduje kontrolki po ich nazwach strukturalnych i typach (np. `child_window(title="New message", control_type="Button")`). Odporne na skalowanie ekranu, motywy jasny/ciemny, rozdzielczości i drobne zmiany UI w aktualizacjach.

```
1. Fokus na okno Phone Link (pywinauto — znajdź po tytule okna)
2. Kliknij "Wiadomości" (jeśli nie jest już otwarte)
3. Kliknij "Nowa wiadomość" (ikona +)
4. Dla każdego numeru w paczce (max 20):
   a. Kliknij pole "Do:"
   b. Wpisz numer
   c. Potwierdź Enter (dodaje odbiorcę)
   d. wait('visible', timeout=10) — dynamiczny wait na pojawienie się tagu odbiorcy
5. Kliknij pole treści wiadomości
6. Zachowaj aktualną zawartość schowka → wklej treść (Ctrl+V) → przywróć schowek
7. Kliknij Wyślij
8. Losowa pauza 4-8s → następna paczka
```

### Zabezpieczenia

- Przed każdą akcją `wait('visible', timeout=10)` — dynamiczne czekanie na element zamiast stałych sleep()
- Jeśli element nie pojawi się w 10s → stop + komunikat
- Ochrona schowka: zapisanie → użycie → przywrócenie zawartości
- Randomizacja opóźnień między paczkami (4-8s) — minimalizuje ryzyko wykrycia przez filtry anty-spam operatora
- Ostrzeżenie w GUI: "Nie ruszaj myszką ani klawiaturą podczas wysyłki. Komputer będzie zablokowany na czas automatyzacji."
- Ostrzeżenie przy dużych wysyłkach: "Wysyłanie dużej liczby SMS-ów z prywatnego numeru może triggerować filtry anty-spam operatora"

## Obsługa błędów

| Błąd | Reakcja |
|------|---------|
| Phone Link nie otwarty / nie znaleziono okna | Próba uruchomienia automatycznie. Jeśli się nie uda → stop + komunikat "Otwórz Phone Link i połącz telefon, potem kliknij Wznów" |
| Telefon niepołączony | Czeka 15s, retry raz. Jeśli dalej nie działa → stop + komunikat |
| Element UI nie znaleziony (UIA nie znajduje kontrolki) | Stop + komunikat "Nie mogę znaleźć elementu X. Sprawdź czy Phone Link jest otwarty i widoczny" |
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
│   └── phone_link.py        # pywinauto UIA logika — sekwencja akcji
├── requirements.txt         # openpyxl, pywinauto, phonenumbers
└── README.md
```

## Technologie

- Python 3.12+
- tkinter (GUI — wbudowane w Python)
- openpyxl (odczyt Excel .xlsx)
- pywinauto z backendem UIA (automatyzacja — znajdowanie kontrolek po nazwie/typie, kliknięcia, wpisywanie, zarządzanie oknami)
- phonenumbers (walidacja numerów PL)

## Przyszła rozbudowa

Architektura z interfejsem `SMSSender` pozwala na dodanie `AdbSender` (Podejście 3) bez zmiany reszty aplikacji. Wymaga tylko nowej klasy implementującej `send(numbers, message)`.

## Ograniczenia

- Wymaga otwartego Phone Link z połączonym telefonem Android
- Użytkownik nie może ruszać myszką podczas wysyłki
- Zależność od UI Phone Link — zmiana nazw kontrolek UIA w aktualizacji może wymagać dostosowania selektorów
- Komputer zablokowany podczas wysyłki (UI automation wymaga fokusa na Phone Link)
- Ryzyko filtrów anty-spam operatora przy dużej liczbie SMS-ów z prywatnego numeru
- Max 20 odbiorców na paczkę (limit Phone Link)
- Polskie numery — walidacja domyślnie dla PL. Akceptuje formaty: `+48512345678`, `48512345678`, `512345678`. Wszystkie normalizowane do formatu `+48XXXXXXXXX` przed wysyłką
