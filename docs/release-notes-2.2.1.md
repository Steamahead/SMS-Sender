# SMS Sender 2.2.1

Wydanie usprawniające **szybkość i niezawodność wysyłki**. Aktualizacja zalecana dla
wszystkich — instalator zachowuje dotychczasowe ustawienia, klucz API i historię.

## ⬇ Pobierz
**`SMSSender_Setup_2.2.1.exe`** — uruchom i podążaj za kreatorem (domyślne ustawienia są OK).

---

## ⚡ Szybkość i niezawodność

- **Szybsza wysyłka.** Aplikacja nie czeka już sztywno po każdym SMS-ie — reaguje od
  razu, gdy Phone Link jest gotowy na kolejną wiadomość. Przy większych listach
  wysyłka kończy się zauważalnie szybciej, bez utraty stabilności.
- **Mniej potknięć na schowku.** Gdy schowek jest chwilowo zajęty przez inny program,
  aplikacja ponawia próbę zamiast przerywać — wysyłka jest odporniejsza na zakłócenia.

---

## 🛠 Dla technicznych

- **Wysyłka:** czekanie warunkowe (`_wait_until`) zamiast sztywnego `sleep(2.0)` po
  otwarciu nowej wiadomości (Ctrl+N) — pętla sprawdza gotowość okna i rusza, gdy tylko
  jest gotowe (commit `4d622fb`).
- **Schowek:** `_open_clipboard` z ponawianiem przy `OpenClipboard` zajętym przez inny
  proces (typowa przyczyna sporadycznych błędów wklejania).
- **Testy:** dodano `tests/conftest.py` (autouse-fixture kierujący `tempfile` do
  pytestowego `tmp_path`) — testy nie zostawiają już katalogów `tmpXXXXXXXX` w projekcie.
  **107 PASS.**

**Pełna lista zmian:** commity `4d622fb`, `a26eb0f` (od `2.2.0`).
