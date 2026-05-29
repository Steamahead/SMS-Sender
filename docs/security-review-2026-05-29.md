# Przegląd bezpieczeństwa — SMS Sender v2.1.2

Data: 2026-05-29 · Zakres: cała aplikacja (core, automation, gui)

Metodyka: analiza pod kątem przechowywania sekretów, danych osobowych (RODO),
wstrzyknięć (SQL/CSV/keystroke), obsługi sieci/TLS, walidacji wejścia.

---

## Krytyczne / wysokie

### H1. Klucz API zapisany jawnym tekstem
`core/settings.py` → `%APPDATA%\SMSSender\settings.json`, pole `gemini_api_key`
przechowuje klucz OpenAI/Anthropic/Gemini w czystym JSON.
- Ryzyko: każdy proces na koncie użytkownika, malware, kopia profilu, backup w
  chmurze (OneDrive sync %APPDATA%), profil roamingowy → odczyt klucza.
  Klucz OpenAI/Anthropic = bezpośrednie obciążenie rachunku atakującego.
- Rekomendacja: szyfrowanie DPAPI (`win32crypt.CryptProtectData` / `pywin32`),
  wiązane z kontem Windows. Minimum: ostrzeżenie w UI + przycisk „wyczyść klucz".

### H2. Dane osobowe w bazie bez szyfrowania (RODO/istotne dla sektora publicznego)
`core/history.py` → `history.db` (SQLite, plaintext) trzyma numery telefonów,
pełną treść SMS-ów oraz `row_data` z importu (imiona, nr spraw — cokolwiek było
w Excelu). Do 1000 sesji, brak funkcji „usuń sesję" / retencji / czyszczenia.
- Kontekst: wysyłka do obywateli z urzędu = dane osobowe pod RODO.
- Rekomendacja: (a) funkcja usuwania pojedynczej sesji + „wyczyść całą historię",
  (b) polityka retencji (np. auto-usuwanie > 90 dni), (c) rozważyć SQLCipher.

## Średnie

### M1. Wstrzyknięcie ENTER przez treść wiadomości (potwierdzony błąd)
`automation/phone_link.py::_escape_for_type_keys` escape'uje `+^%~{}()`, ale NIE
`\n` ani `\t`. Pole wiadomości to `QTextEdit` (wielolinijkowy). `type_keys`
interpretuje `\n` jako ENTER → w Phone Link ENTER **wysyła** SMS-a → wiadomość
wieloliniowa zostaje wysłana ucięta, a reszta wpisana w zepsuty stan.
- To zarazem błąd funkcjonalny i wektor „keystroke injection".
- Rekomendacja: wklejać treść przez schowek (`_set_clipboard` + Ctrl+V) zamiast
  `type_keys` — odporne na `\n`, polskie znaki i znaki sterujące. Alternatywnie
  zamienić `\r\n`/`\n` na `{ENTER}`-bezpieczny odpowiednik lub odrzucać newline.

### M2. CSV/Excel formula injection przy eksporcie raportu
`core/report.py` zapisuje `message`/`error`/`number` bez sanitacji. Treść
zaczynająca się od `= + - @` zostanie wykonana jako formuła po otwarciu w Excelu
(także xlsx). Treść SMS i komunikaty wyjątków są kontrolowane przez dane wejściowe.
- Rekomendacja: poprzedzać komórki ryzykowne apostrofem (`'`) lub spacją.

## Niskie / informacyjne

- **L1.** Klucz Gemini przekazywany w URL (`?key=...`) — schemat wymagany przez
  Google, ale URL-e trafiają do logów proxy/AV. Akceptowalne, do świadomości.
- **L2.** Brak limitu rozmiaru/wierszy importu — bardzo duży plik = wysokie
  zużycie RAM. Lokalna apka, niskie ryzyko.
- **L3.** `_save/_set/_restore_clipboard` połykają wszystkie wyjątki po cichu —
  utrudnia diagnostykę, nie jest luką.

## Zweryfikowano jako BEZPIECZNE ✅

- **SQL**: `core/history.py` wszędzie używa zapytań parametryzowanych — brak SQLi.
- **TLS**: `urllib` z domyślną weryfikacją certyfikatu (nie wyłączona) w `ai_refine.py`.
- **Ścieżki**: pliki wybiera użytkownik przez dialog — brak path traversal.
- **Parsowanie odpowiedzi modelu**: regex `\{.*\}` liniowy, JSON ograniczony max_tokens — brak ReDoS.
- **Lokalizacja danych**: `%APPDATA%\SMSSender` — per-user (rozsądny domyślny izolator).

---

## Priorytety napraw
1. M1 (błąd funkcjonalny + bezpieczeństwo — psuje wieloliniowe SMS-y) — najpierw.
2. H2 (RODO — funkcja usuwania historii) — istotne dla kontekstu urzędowego.
3. H1 (szyfrowanie klucza API DPAPI).
4. M2 (sanitacja eksportu CSV).
