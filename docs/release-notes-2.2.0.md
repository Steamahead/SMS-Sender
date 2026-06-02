# SMS Sender 2.2.0

Wydanie skupione na **bezpieczeństwie danych** oraz drobnych usprawnieniach interfejsu.
Aktualizacja zalecana dla wszystkich użytkowników — instalator zachowuje dotychczasowe
ustawienia, klucz API i historię.

## ⬇ Pobierz
**`SMSSender_Setup_2.2.0.exe`** — uruchom i podążaj za kreatorem (domyślne ustawienia są OK).

---

## 🔒 Bezpieczeństwo

- **Klucz API szyfrowany na dysku.** Klucz (Gemini/OpenAI/Anthropic) nie jest już
  przechowywany czystym tekstem — jest szyfrowany mechanizmem Windows (DPAPI),
  powiązanym z Twoim kontem użytkownika. Stary klucz zostaje automatycznie
  zaszyfrowany przy pierwszym uruchomieniu — nic nie musisz robić.
- **Zarządzanie historią (RODO).** W zakładce *Historia* możesz teraz **usunąć
  pojedynczą sesję** lub **wyczyścić całą historię**. Dodatkowo sesje starsze niż
  **90 dni** są usuwane automatycznie. Ważne, bo historia zawiera numery telefonów
  i treści wiadomości (dane osobowe).
- **Bezpieczny eksport raportów.** Raporty CSV/Excel są zabezpieczone przed
  „formula injection" — złośliwa treść nie wykona się jako formuła po otwarciu w Excelu.

## ✨ Usprawnienia

- **Wieloliniowe SMS-y działają poprawnie.** Wiadomości z przejściem do nowej linii
  były wcześniej wysyłane ucięte — teraz treść jest wklejana w całości. Przy okazji
  lepsza obsługa polskich znaków.
- **Wpisywanie numeru ręcznie u góry.** Pole „wpisz numer + Dodaj" przeniesione na
  górę listy odbiorców, obok wczytywania pliku Excel — bardziej intuicyjnie.
- **Godzina w szczegółach historii.** Szczegóły sesji pokazują teraz godzinę
  (GG:MM:SS) wysłania każdego SMS-a obok statusu.

---

## 🛠 Dla technicznych

- Klucz API: Windows DPAPI (`CryptProtectData`, scope użytkownika), format `dpapi:<base64>`,
  z migracją legacy plaintextu i fallbackiem (`core/crypto_store.py`).
- Historia: `delete_session()`, `clear_all()`, retencja `RETENTION_DAYS=90` (auto-purge przy zapisie).
- Phone Link: treść wklejana przez schowek (Ctrl+V) zamiast `type_keys` — odporne na `\n`
  i znaki sterujące; schowek użytkownika jest zapisywany i przywracany wokół wysyłki.
- Eskport: `_sanitize_cell()` poprzedza apostrofem pola zaczynające się od `= + - @`.
- Nowa zależność: `pywin32` (dla DPAPI; dołączona do buildu PyInstaller).
- Testy: **98 PASS** (było 85). Pełny audyt: `docs/security-review-2026-05-29.md`.

**Pełna lista zmian:** commit `06d045c`.
