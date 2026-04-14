# SMS Sender v2 — Status

## Aktualny stan: GOTOWE — do dalszego testowania i polishu

## Zrealizowane funkcjonalnosci
- Import numerow: Excel/CSV z auto-detekcja kolumny, drag & drop, Ctrl+V ze schowka
- Reczne wpisywanie numerow telefonu (pole + przycisk Dodaj)
- Personalizacja wiadomosci: zmienne {Imie}, {Firma} mapowane na kolumny
- Szablony SMS: zapis/odczyt/usuwanie (JSON)
- Historia wysylki: SQLite, max 1000 sesji
- Raport po wysylce: eksport XLSX/CSV
- Podglad odbiorcow: tabela z checkboxami, zaznacz/odznacz wszystkie
- Checkboxy zachowuja stan przy edycji wiadomosci (nie resetuja sie)
- Deduplikacja numerow
- Licznik SMS (znaki + ilosc SMS-ow)
- Zapamietywanie ustawien (JSON)
- Ikona aplikacji (dymek SMS)
- Polskie znaki w calym UI
- Poprawna odmiana polskich liczebnikow (1 numer, 2 numery, 5 numerow)

## Build
- Exe: `dist/SMSSender/SMSSender.exe` (PyInstaller)
- Rebuild: `python installer/build.py`
- Installer Windows: `installer/sms_sender.iss` (wymaga Inno Setup na komputerze)

## Testy: 85/85 PASS
```
pytest tests/ -v
```

## Nastepne kroki
- Dalsze testy manualne z prawdziwymi numerami
- Instalator Inno Setup (jesli potrzebny)
- README
