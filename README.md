# SMS Sender

Aplikacja desktopowa do masowej wysyłki SMS z komputera z systemem Windows, przez oficjalną aplikację **Łącze z telefonem** (Phone Link) i telefon z Androidem.

Stworzona z myślą o organizacjach pozarządowych (NGO), fundacjach, klubach i małych firmach, które chcą wysłać kilkadziesiąt lub kilkaset spersonalizowanych SMS‑ów bez kupowania bramki SMS.

> **Projekt Fundacji Full Steam Ahead** — bezpłatne narzędzie dla każdego.
> Kontakt: kontakt@fullsteam.pl | Repozytorium: https://github.com/Steamahead/SMS-Sender

---

## Pobierz i zainstaluj

**[⬇ Pobierz instalator (SMSSender_Setup_2.1.1.exe)](https://github.com/Steamahead/SMS-Sender/releases/latest)**

1. Kliknij link powyżej
2. Uruchom pobrany plik `SMSSender_Setup_2.1.1.exe`
3. Podążaj za kreatorem — domyślne ustawienia są OK

> **Uwaga:** Windows SmartScreen może ostrzec o „nieznanym wydawcy" — kliknij *Więcej informacji* → *Uruchom mimo to*. Aplikacja nie jest podpisana certyfikatem komercyjnym, ale jest w pełni bezpieczna — kod źródłowy jest publiczny w tym repozytorium.

---

## Co potrafi

- Import listy numerów z pliku **Excel (.xlsx)** lub **CSV** — automatycznie wykrywa kolumnę z numerami
- **Przeciągnij i upuść** plik na okno aplikacji
- **Wklej ze schowka** (Ctrl+V) — np. skopiowaną kolumnę z Excela
- **Ręczne dodawanie** pojedynczych numerów
- **Personalizacja** wiadomości zmiennymi `{Imie}`, `{Firma}` itp. — podstawiane z kolumn w Excelu
- **Szablony SMS** — zapis, odczyt, usuwanie
- **Podgląd odbiorców** — tabela z checkboxami (zaznacz/odznacz dowolnych adresatów)
- **Licznik znaków i SMS‑ów** — wiesz, ile wiadomości pójdzie
- **Deduplikacja** numerów
- **Historia wysyłek** (SQLite) — max 1000 sesji
- **Raport po wysyłce** — eksport do XLSX lub CSV
- **Zapamiętywanie ustawień** między uruchomieniami
- Pełna **obsługa polskich znaków** (ą, ę, ś, ć, ź, ż, ó, ł, ń) w UI i w wiadomościach
- **Asystent AI (Gemini)** — opcjonalny: kliknięcie „🪄 Popraw AI" generuje trzy warianty SMS-a (korekta, formalny, przyjazny) do wyboru

---

## Asystent AI — opcjonalna „magiczna różdżka"

W panelu treści SMS możesz włączyć asystenta AI, który poprawi gramatykę, interpunkcję i ton wiadomości. Kliknięcie różdżki generuje **trzy warianty**:

- **Korekta** — minimalna poprawa oryginału (gramatyka, interpunkcja, polskie znaki)
- **Formalny** — urzędowy, profesjonalny ton
- **Przyjazny** — ciepły, ludzki, bezpośredni

Wybierasz wariant, który najbardziej Ci pasuje, jednym kliknięciem. Placeholdery typu `{imie}` są zawsze zachowywane.

### Konfiguracja w 3 krokach (jednorazowo)

1. Wejdź na **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)** i zaloguj się kontem Google
2. Kliknij **„Create API key"** — wygeneruj klucz (darmowy plan Gemini ma hojny limit, ~1500 zapytań dziennie)
3. W aplikacji otwórz zakładkę **Ustawienia**, wklej klucz, zaznacz „Włącz asystenta AI", kliknij **Zapisz**

Klucz API zapisany jest **lokalnie na Twoim komputerze** (w `%APPDATA%\SMSSender\settings.json`) i nigdy nie opuszcza Twojego komputera poza wywołania do Gemini.

> **Uwaga:** treść SMS-a wysyłana do AI trafia na serwery Google. **Nie wysyłaj danych wrażliwych** (PESEL, dane medyczne, hasła) — używaj AI tylko do tekstów ogólnych (zaproszenia, powiadomienia, przypomnienia).

---

## Wymagania

- **Windows 10** lub **Windows 11**
- **Telefon z Androidem** z zainstalowaną aplikacją **Link do Windows** (*Link to Windows*)
- **Łącze z telefonem** (*Phone Link*) na komputerze — wbudowane w Windows 11, w Windows 10 dostępne w Microsoft Store
- Telefon sparowany z komputerem i **z włączoną opcją wysyłania SMS**

---

## Instalacja

1. Pobierz instalator ze strony [Releases](https://github.com/Steamahead/SMS-Sender/releases/latest)
2. Uruchom plik `SMSSender_Setup_2.1.1.exe` — podążaj za kreatorem (domyślne ustawienia są OK)
3. Opcjonalnie zaznacz **„Utwórz ikonę na pulpicie"**
4. Po instalacji aplikacja startuje automatycznie

**Uwaga:** Windows SmartScreen może ostrzec o „nieznanym wydawcy" — kliknij *Więcej informacji* → *Uruchom mimo to*. Aplikacja nie jest podpisana certyfikatem (certyfikaty kosztują kilkaset euro rocznie), ale jest bezpieczna — kod źródłowy dostępny w tym repozytorium.

---

## Pierwsze uruchomienie — sparowanie telefonu

Zanim użyjesz SMS Sender, **upewnij się, że Łącze z telefonem działa i potrafi wysłać SMS ręcznie**:

1. Otwórz **Łącze z telefonem** na komputerze
2. Sparuj telefon (zeskanuj QR kod aplikacją *Link do Windows* na Androidzie)
3. W Łączu z telefonem przejdź do zakładki **Wiadomości**
4. Wyślij testowy SMS do siebie — **musi zadziałać**
5. Dopiero wtedy uruchom SMS Sender

Jeśli Łącze z telefonem nie potrafi wysłać SMS, SMS Sender też nie wyśle — aplikacja automatyzuje ten sam proces.

---

## Jak używać

### 1. Przygotuj listę odbiorców

Utwórz plik Excel z kolumnami np.:

| Imie      | Firma            | Telefon      |
|-----------|------------------|--------------|
| Anna      | Fundacja XYZ     | +48500600700 |
| Jan       | Stowarzyszenie Z | 600700800    |

Kolumna z numerami telefonu może nazywać się dowolnie (`Telefon`, `Nr`, `Phone`, itp.) — aplikacja sama ją wykryje. Numery mogą być z prefiksem `+48` lub bez.

### 2. Zaimportuj listę

- **Przeciągnij** plik na okno aplikacji, **lub**
- Kliknij **Importuj plik** i wybierz plik, **lub**
- Skopiuj kolumnę numerów w Excelu i wklej **Ctrl+V**, **lub**
- Wpisz numer ręcznie i kliknij **Dodaj**

### 3. Napisz wiadomość

- Wpisz treść w polu wiadomości
- Możesz użyć zmiennych: `Witaj {Imie}! Zapraszamy z {Firma} na spotkanie.`
- Licznik na dole pokazuje liczbę znaków i SMS‑ów
- Zapisz treść jako szablon jeśli będziesz jej używać częściej

### 4. Podejrzyj odbiorców

- Tabela pokazuje każdego odbiorcę i finalny tekst SMS
- Odznacz checkboxami adresatów, do których **nie** chcesz wysyłać

### 5. Wyślij

- Kliknij **Wyślij SMS**
- **Nie dotykaj myszy ani klawiatury** — aplikacja klika w Łączu z telefonem
- Okno Łącza z telefonem musi być widoczne (nie zminimalizowane)
- Po zakończeniu możesz wyeksportować raport

---

## Najczęstsze problemy

### „Nie znaleziono Łącza z telefonem"
Uruchom Łącze z telefonem ręcznie i zostaw otwarte, potem wysyłaj.

### Pierwsze SMS‑y wyszły, potem błąd
Łącze z telefonem czasem zgubi okno wiadomości. Zamknij je i otwórz ponownie.

### Numery z `+48` nie działają
Nieprawda — Phone Link akceptuje numery w formacie `+48500600700`. Nie usuwaj prefiksu.

### Polskie znaki wysyłają się jako „?"
Sprawdź, czy telefon ma kodowanie UTF‑8 dla SMS‑ów. W większości nowoczesnych Androidów jest domyślnie.

### Windows SmartScreen blokuje instalator
Kliknij *Więcej informacji* → *Uruchom mimo to*. Aplikacja nie jest podpisana certyfikatem.

### Antywirus oznacza exe jako zagrożenie
PyInstaller generuje binaria podobne do niektórych malware — to fałszywy alarm. Dodaj wyjątek lub pobierz kod źródłowy i zbuduj sam.

---

## Dla deweloperów

### Uruchomienie z kodu źródłowego

```bash
git clone https://github.com/Steamahead/SMS-Sender.git
cd SMS-Sender
pip install -r requirements.txt
python main.py
```

### Testy
```bash
pytest tests/ -v
```

### Budowanie exe
```bash
python installer/build.py
```

Output: `dist/SMSSender/SMSSender.exe`

### Budowanie instalatora Windows
Wymaga **Inno Setup 6** (https://jrsoftware.org/isdl.php):

```bash
iscc installer/sms_sender.iss
```

Output: `dist/installer/SMSSender_Setup_2.1.1.exe`

### Stos technologiczny
- Python 3.11+
- PySide6 (Qt) — GUI
- pywinauto (UIA) — automatyzacja Łącza z telefonem
- openpyxl — Excel I/O
- pytest — testy (85 testów)

### Struktura
```
core/          — logika biznesowa (import, personalizacja, historia, raporty)
automation/    — pywinauto UIA — sterowanie Phone Link
gui/           — okno, taby, widżety, style QSS
installer/     — build.py, sms_sender.iss, icon.ico
tools/         — pomocnicze skrypty debugowania
tests/         — 85 testów pytest
```

---

## Licencja

**MIT License** — możesz używać, kopiować, modyfikować i rozpowszechniać aplikację swobodnie, w tym w celach komercyjnych. Pełny tekst licencji: plik [LICENSE](LICENSE).

Aplikacja nie wysyła żadnych danych na zewnątrz — cała wysyłka idzie lokalnie przez Łącze z telefonem i telefon użytkownika.

---

## Uwagi

- Aplikacja **nie jest bramką SMS** — wysyła przez **Twój prywatny telefon**. Każdy SMS kosztuje zgodnie z Twoim abonamentem operatora.
- Nie używaj do spamu. Masz obowiązek uzyskać zgodę odbiorców na wysyłanie wiadomości (RODO, ustawa o świadczeniu usług drogą elektroniczną).
- Przy dużych listach (>200 numerów) Phone Link może się zawieszać — rób paczki po 50–100.
