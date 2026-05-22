"""Gemini-based SMS refiner. Returns three style variants of a draft message.

Uses the stdlib only (urllib + json) so no extra PyInstaller deps.
"""
import json
import urllib.request
import urllib.error


GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
REQUEST_TIMEOUT = 30

VARIANT_KEYS = ("korekta", "formalny", "przyjazny")

SYSTEM_PROMPT = """Jesteś asystentem do poprawiania krótkich wiadomości SMS po polsku.
Otrzymasz tekst SMS-a wpisany przez urzędnika. Zwróć DOKŁADNIE trzy warianty:

1. KOREKTA — minimalna poprawa oryginału: gramatyka, interpunkcja, ortografia,
   polskie znaki. Zachowaj styl, ton i długość zbliżone do oryginału.
2. FORMALNY — ton urzędowy, uprzejmy, profesjonalny. Pełne zdania, grzecznościowe
   zwroty (np. „Uprzejmie informujemy", „Z poważaniem").
3. PRZYJAZNY — ciepły, ludzki, bezpośredni ton. Naturalny, bez sztywności,
   ale wciąż uprzejmy.

REGUŁY:
- Zawsze zachowuj WSZYSTKIE placeholdery w klamrach typu {imie}, {numer}, {nazwa}
  — NIE zmieniaj nazw ani liczby placeholderów.
- Każdy wariant musi być pełnym, gotowym do wysłania SMS-em tekstem.
- Bez emoji, bez markdownu, bez cudzysłowów wokół treści.
- Odpowiedź zwróć WYŁĄCZNIE jako JSON o strukturze:
  {"korekta": "...", "formalny": "...", "przyjazny": "..."}
- Bez żadnego tekstu przed ani po JSON-ie."""


class AIRefineError(Exception):
    pass


def refine_message(api_key: str, text: str, timeout: int = REQUEST_TIMEOUT) -> dict:
    """Send `text` to Gemini and return {'korekta': str, 'formalny': str, 'przyjazny': str}.

    Raises AIRefineError with a user-friendly message on any failure.
    """
    if not api_key or not api_key.strip():
        raise AIRefineError("Brak klucza API. Wprowadź klucz w zakładce Ustawienia.")
    if not text or not text.strip():
        raise AIRefineError("Pole wiadomości jest puste — wpisz wstępną treść SMS-a.")

    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": text.strip()}]}],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json",
        },
    }
    body = json.dumps(payload).encode("utf-8")

    url = f"{GEMINI_ENDPOINT}?key={api_key.strip()}"
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        if e.code == 400:
            raise AIRefineError(f"Błąd zapytania (400). Sprawdź klucz API.\n{detail[:300]}")
        if e.code == 403:
            raise AIRefineError("Klucz API odrzucony (403). Sprawdź czy klucz jest aktywny.")
        if e.code == 429:
            raise AIRefineError("Przekroczono limit zapytań (429). Spróbuj za chwilę.")
        raise AIRefineError(f"Błąd HTTP {e.code}: {detail[:300]}")
    except urllib.error.URLError as e:
        raise AIRefineError(f"Błąd połączenia z Gemini API: {e.reason}")
    except TimeoutError:
        raise AIRefineError(f"Timeout po {timeout}s — sprawdź połączenie.")

    return _parse_response(raw)


def _parse_response(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AIRefineError(f"Nieprawidłowa odpowiedź API: {e}")

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise AIRefineError("Pusta odpowiedź modelu — spróbuj ponownie.")

    try:
        variants = json.loads(text)
    except json.JSONDecodeError:
        raise AIRefineError(f"Model zwrócił nieprawidłowy JSON: {text[:200]}")

    if not isinstance(variants, dict):
        raise AIRefineError(f"Oczekiwano obiektu JSON, otrzymano: {type(variants).__name__}")

    result = {}
    for key in VARIANT_KEYS:
        value = variants.get(key)
        if not value or not isinstance(value, str):
            raise AIRefineError(f"Brak wariantu „{key}” w odpowiedzi modelu.")
        result[key] = value.strip()
    return result
