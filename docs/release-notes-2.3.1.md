# SMS Sender 2.3.1

**Jeśli używasz personalizacji (`{Imie}`, `{Firma}`) — zaktualizuj koniecznie.** Instalator
zachowuje dotychczasowe ustawienia, klucz API, szablony i historię.

## ⬇ Pobierz
**`SMSSender_Setup_2.3.1.exe`** — uruchom i podążaj za kreatorem (domyślne ustawienia są OK).

---

## 🐞 Naprawione błędy

### Personalizacja nie trafiała do odbiorców
Podgląd pokazywał „Cześć Anna”, ale **do ludzi wychodził surowy szablon** — każdy dostawał
dosłownie „Cześć {Imie}”. Teraz każdy odbiorca dostaje swoją wersję wiadomości, dokładnie
taką jak w kolumnie „Gotowa treść”.

### Imiona przesuwały się po usunięciu duplikatu
Gdy w pliku ten sam numer występował dwa razy, aplikacja usuwała duplikat, ale nie jego
wiersz z danymi. Od tego miejsca każdy kolejny numer dostawał **imię poprzedniej osoby**.
Naprawione.

### Pliki CSV z polskiego Excela
Excel z polskimi ustawieniami zapisuje CSV ze **średnikiem** i w kodowaniu Windows-1250.
Takie pliki kończyły się „Błędem importu” albo lądowały w jednej kolumnie, a nagłówki CSV
nie były w ogóle czytane — więc `{Imie}` nie działało. Teraz działają CSV z przecinkiem,
średnikiem i tabulatorem, w UTF-8 i Windows-1250.

### Drobne
- Zaznaczone pola wyboru i kółka wyboru wariantu AI były **niewidoczne**.
- Przycisk „✕” (usuń numer z listy) był pustym kwadratem.
- Wyłączony przycisk „Rozpocznij wysyłkę” miał szary napis na szarym tle.

---

## ✨ Nowości

### Dłuższe wiadomości i uczciwy licznik
- Limit treści: **700 znaków** (było 500).
- Licznik pokazuje, ile **części SMS** policzy operator. Dotąd każda wiadomość powyżej
  160 znaków była liczona jako „2 SMS”, a w rzeczywistości 700 znaków z polskimi literami
  to **11 części**.
- **„Bez polskich znaków”** — jedno kliknięcie zamienia ą→a, ł→l itd. (oraz cudzysłowy
  i myślniki wstawiane przez Worda czy asystenta AI). Jeden SMS mieści wtedy 160 znaków
  zamiast 70, więc długa wiadomość kosztuje **około 2× mniej**.

### Bezpieczniejsza wysyłka
- **„Wyślij test do siebie”** — jeden SMS na Twój numer, z treścią spersonalizowaną dla
  pierwszego odbiorcy. Nie trafia do historii i nie czyści listy.
- **Potwierdzenie przed wysyłką** z liczbą odbiorców i części SMS oraz przyciskiem
  „Anuluj”. Ostrzega, gdy w wiadomości została niepodmieniona zmienna albo gdy jest tak
  długa, że telefon może wysłać ją jako MMS.
- **Ostrzeżenie o literówce w zmiennej** — wpiszesz `{imie}`, a w pliku jest `Imię`?
  Pod polem treści pojawi się „chodziło o {Imię}?”.

### Wygodniejsze numery
- **Kilka numerów w jednej komórce** Excela (po przecinku, średniku albo Alt+Enter) —
  przy wklejaniu Ctrl+V i przy imporcie pliku. Z wklejonego wiersza brane są wszystkie
  numery, nie tylko pierwszy.
- **Pole ręczne przyjmuje kilka numerów naraz**: `512 345 678; 600-700-800`. Błędny
  fragment zostaje w polu, podświetlony do poprawy.
- Pominięte wpisy są wymienione w pasku stanu, zamiast znikać bez śladu.

### Rozciągane okna
- Panele na zakładkach **Wysyłka** i **Historia** rozdzielają przeciągane paski; układ
  jest zapamiętywany.
- Każde pole z tekstem ma **uchwyt w prawym dolnym rogu**: w oknie głównym powiększa pole
  kosztem sąsiednich paneli, w okienkach zmienia rozmiar całego okienka.
- Historia pokazuje pełną treść SMS-a zaznaczonej sesji w osobnym panelu.
- Okno wariantów AI pokazuje pełne teksty (dotąd ~2,5 linijki z niełapalnym suwakiem)
  i da się je rozciągać.

---

## 🛠 Dla technicznych

- `send_batch(numbers, message)` przyjmuje `message` jako tekst albo funkcję
  `numer → tekst`. Logika UIA w `automation/phone_link.py` bez zmian.
- Teksty dla odbiorców są zamrażane w chwili startu wysyłki (`SendPanel._texts`), więc
  edycja treści w trakcie lub przed „Wznów” nie zmienia tego, co dostaną pozostali.
- Nowe: `core/sms_counter.py` (GSM-7 160/153, znaki rozszerzone ×2, UCS-2 70/67, `strip_polish`),
  `excel_importer.read_csv_rows` / `extract_phone_numbers` / `deduplicate_with_rows`,
  `personalizer.render_for_numbers` / `unresolved_variables`,
  `gui/widgets/resize_grip.py`.
- **Testy:** 175 PASS (było 128).

**Pełna lista zmian:** od `2.2.2`.
