# SMS Sender — Project Reference

## Cel
Desktopowa aplikacja do wysyłania SMS-ów z komputera przez Windows Phone Link. Numery z Excela, wysyłka w paczkach po max 20 odbiorców. Darmowe — SMS-y z prywatnego numeru (Android).

## Architektura
```
ExcelImporter → BatchManager → SMSSender (ABC) → PhoneLinkSender → pywinauto UIA → Phone Link
                                                   └─ (future: AdbSender)
GUI (tkinter) ← orchestruje powyższe moduły
```

## Moduły
| Moduł | Plik | Rola |
|-------|------|------|
| ExcelImporter | `core/excel_importer.py` | Import .xlsx/.csv, walidacja numerów PL (phonenumbers), normalizacja do +48XXXXXXXXX |
| BatchManager | `core/batch_manager.py` | Paczki ≤20, status tracking (pending/sent/error), resume |
| SMSSender ABC | `core/sender.py` | Interfejs abstrakcyjny + PhoneLinkSender wrapper |
| PhoneLinkSender | `automation/phone_link.py` | pywinauto UIA: fokus okna → Messages → New message → dodaj odbiorców → Ctrl+V treść → Send |
| GUI | `gui/app.py` | tkinter: import, edycja treści (160 znaków), podgląd paczek, send/stop/resume, progress bar, log |
| Entry point | `main.py` | Uruchamia SMSSenderApp |

## Tech Stack
Python 3.11+, tkinter, openpyxl, pywinauto (UIA backend), phonenumbers

## Testy
- `tests/test_excel_importer.py` — 17 testów (normalize, validate, import excel/csv)
- `tests/test_batch_manager.py` — 9 testów (split, status, resume, summary)
- `tests/test_sender.py` — 3 testy (ABC contract, FakeSender)

## Kluczowe decyzje
- **pywinauto UIA** (nie Win32) — odporne na skalowanie/motywy/rozdzielczości
- **Clipboard protection** — save → use → restore
- **Ctrl+V** zamiast type_keys — obsługuje polskie znaki
- **Randomizacja 4-8s** między paczkami — anty-spam
- **Lazy import** PhoneLinkAutomation w sender.py — nie wymaga pywinauto przy testach

## Selektory UIA (mogą wymagać dostosowania)
```python
"Messages" (TabItem) → "New message" (Button) → "To" (Edit) → Edit#2 (pole treści) → "Send" (Button)
```
Jeśli Phone Link jest po polsku, nazwy mogą być inne. Użyj `win.print_control_identifiers()` do discovery.

## Ograniczenia
- Wymaga otwartego Phone Link z połączonym Android
- Komputer zablokowany podczas wysyłki (UI automation wymaga fokusa)
- Max 20 odbiorców/paczka (limit Phone Link)
- Ryzyko filtrów anty-spam operatora przy dużych wysyłkach
