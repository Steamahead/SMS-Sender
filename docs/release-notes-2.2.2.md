# SMS Sender 2.2.2

Wydanie naprawcze. **Jeśli masz 2.2.1 — zaktualizuj koniecznie.** Instalator zachowuje
dotychczasowe ustawienia, klucz API i historię.

## ⬇ Pobierz
**`SMSSender_Setup_2.2.2.exe`** — uruchom i podążaj za kreatorem (domyślne ustawienia są OK).

---

## 🐞 Naprawiony błąd: pierwszy odbiorca nie dostawał SMS-a

W wersji 2.2.1 przy pierwszej wysyłce po uruchomieniu aplikacji **pierwszy numer z listy
bywał pomijany**: w Phone Link otwierało się okno nowej wiadomości, ale numer i treść nie
były w nie wpisywane. Aplikacja mimo to raportowała paczkę jako wysłaną, więc po ponownym
kliknięciu „Rozpocznij wysyłkę" ten numer był traktowany jako obsłużony.

Przyczyna: aplikacja ruszała z wpisywaniem, zanim okno nowej wiadomości było gotowe na
przyjęcie tekstu. Przy pierwszej wiadomości Phone Link otwiera je najwolniej — i właśnie
tam pierwsze znaki przepadały.

**Co się zmieniło:**

- Aplikacja czeka teraz, aż pole „Do" faktycznie będzie gotowe, zanim cokolwiek wpisze.
- Pole treści jest **klikane**, a nie wyszukiwane tabulatorem. Dotąd aplikacja zakładała,
  że po zatwierdzeniu numeru dwa naciśnięcia Tab trafią w pole wiadomości — przy zimnym
  oknie nie trafiały i treść wklejała się w próżnię.
- Przed wysłaniem **sprawdza**, czy numer i treść naprawdę znalazły się w oknie. Jeśli nie
  — powtarza próbę (do 3 razy). Ponowienie następuje zawsze **przed** wysłaniem, więc
  żaden SMS nie zostanie wysłany dwa razy.
- Jeżeli mimo prób numer się nie uda, jest oznaczony w raporcie jako **błąd** — nigdy
  więcej jako „wysłany".

---

## 📋 Dokładniejszy raport i mądrzejsze „Wznów"

- **Wynik liczony dla każdego numeru osobno**, a nie dla całej 20-numerowej paczki. Dotąd
  jeden nieudany numer albo psuł statystykę całej paczki, albo — gorzej — chował się
  wśród udanych.
- **Jeden problematyczny numer nie przerywa całej wysyłki.** Reszta listy idzie dalej,
  a nieudane numery lądują w raporcie.
- **„Wznów" ponawia wyłącznie numery, które się nie udały** (plus te, do których wysyłka
  jeszcze nie dotarła). Wcześniej wznowienie powtarzało całą paczkę — czyli wysyłało
  duplikaty do osób, które SMS-a już dostały.

---

## 🛠 Dla technicznych

- `automation/phone_link.py`: nowe `_wait_for_compose()` czeka na aktywne, widoczne pole
  „Do" w panelu nowej wiadomości. Zastępuje `_reacquire_window()`, które czekało jedynie
  na **główne** okno Phone Link — a to zawsze istnieje, więc wracało natychmiast
  (regresja z `4d622fb`, gdzie zdjęto `sleep(2.0)` po Ctrl+N).
- Weryfikacja przed `ENTER`: `_verify_recipient()` porównuje cyfry w polu „Do”
  z numerem, `_verify_message()` sprawdza niepustą treść. Odczyt przez ValuePattern
  (`get_value` / `legacy_properties`), nigdy przez `window_text()` — dla pól UIA zwraca
  ono placeholder, więc puste pole wyglądałoby na wypełnione. Gdy wartości nie da się
  odczytać, weryfikacja loguje ostrzeżenie i przepuszcza (nie blokuje wysyłki).
- Pole treści lokalizowane i klikane (`_MSG_FIELD_RE` + `click_input()`) zamiast
  `{TAB}{TAB}`. Weryfikacja treści odpytuje pole przez ~3 s zamiast jednego strzału —
  wklejenie do WinUI potrafi pojawić się z opóźnieniem.
- `_send_single(..., attempts=3)` ponawia całe komponowanie; `_reset_compose()` zamyka
  niedokończony panel przed kolejną próbą.
- `send_batch(..., on_result=)` raportuje każdego odbiorcę osobno. Bez callbacku błędy
  nadal podnoszą wyjątek na koniec paczki — nie mogą przejść jako sukces.
- `BatchManager.next_pending_index(skip=…)` — paczka w stanie „error" nie jest
  serwowana w kółko w tej samej pętli wysyłki.
- `SendPanel._owed_numbers()` buduje listę do wznowienia z nieudanych odbiorców
  i nietkniętych paczek.
- **Testy:** `tests/test_phone_link_send.py` (atrapa Phone Linka odtwarzająca zimny
  start — panel pojawia się po kilku skanach UIA i gubi klawisze pierwszego compose)
  oraz `tests/test_send_loop_results.py`. **124 PASS.**

**Pełna lista zmian:** od `2.2.1`.
