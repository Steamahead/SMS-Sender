"""Multi-provider LLM client for SMS refinement.

Auto-detects provider (Gemini / OpenAI / Anthropic) by API-key prefix and
calls the matching HTTP endpoint. Stdlib only (urllib + json) — no extra
PyInstaller deps. All providers return the same shape:
{'korekta': str, 'formalny': str, 'przyjazny': str}
"""
import json
import re
import urllib.request
import urllib.error


GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

OPENAI_MODEL = "gpt-4o-mini"
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

ANTHROPIC_MODEL = "claude-haiku-4-5"
ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

REQUEST_TIMEOUT = 30
VARIANT_KEYS = ("korekta", "formalny", "przyjazny")

PROVIDER_LABELS = {
    "gemini": "Google Gemini",
    "openai": "OpenAI",
    "anthropic": "Anthropic Claude",
}

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


def detect_provider(api_key: str) -> str:
    """Identify provider from key prefix. Defaults to Gemini for unknown formats."""
    key = api_key.strip()
    if key.startswith("sk-ant-"):
        return "anthropic"
    if key.startswith("sk-"):
        return "openai"
    return "gemini"


def refine_message(api_key: str, text: str, timeout: int = REQUEST_TIMEOUT) -> dict:
    """Send `text` to the detected provider; return three variants."""
    if not api_key or not api_key.strip():
        raise AIRefineError("Brak klucza API. Wprowadź klucz w zakładce Ustawienia.")
    if not text or not text.strip():
        raise AIRefineError("Pole wiadomości jest puste — wpisz wstępną treść SMS-a.")

    provider = detect_provider(api_key)
    text = text.strip()

    if provider == "gemini":
        return _call_gemini(api_key.strip(), text, timeout)
    if provider == "openai":
        return _call_openai(api_key.strip(), text, timeout)
    if provider == "anthropic":
        return _call_anthropic(api_key.strip(), text, timeout)
    raise AIRefineError(f"Nieznany typ klucza API: {provider}")


def _http_post(url: str, headers: dict, payload: dict, timeout: int, provider_name: str) -> str:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        if e.code in (400, 401):
            raise AIRefineError(
                f"{provider_name} odrzucił klucz API ({e.code}). "
                f"Sprawdź czy klucz jest poprawny.\n{detail[:300]}"
            )
        if e.code == 403:
            raise AIRefineError(
                f"{provider_name}: klucz API odrzucony (403). Sprawdź czy jest aktywny "
                f"i czy ma dostęp do wybranego modelu."
            )
        if e.code == 429:
            raise AIRefineError(
                f"{provider_name}: przekroczono limit zapytań (429). Spróbuj za chwilę."
            )
        raise AIRefineError(f"{provider_name} — błąd HTTP {e.code}: {detail[:300]}")
    except urllib.error.URLError as e:
        raise AIRefineError(f"Błąd połączenia z {provider_name}: {e.reason}")
    except TimeoutError:
        raise AIRefineError(f"Timeout po {timeout}s ({provider_name}) — sprawdź połączenie.")


def _call_gemini(api_key: str, text: str, timeout: int) -> dict:
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json",
        },
    }
    raw = _http_post(
        f"{GEMINI_ENDPOINT}?key={api_key}",
        {"Content-Type": "application/json"},
        payload,
        timeout,
        "Google Gemini",
    )
    data = _safe_json(raw, "Gemini")
    try:
        content = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise AIRefineError("Gemini zwrócił pustą odpowiedź — spróbuj ponownie.")
    return _extract_variants(content)


def _call_openai(api_key: str, text: str, timeout: int) -> dict:
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
    }
    raw = _http_post(
        OPENAI_ENDPOINT,
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        payload,
        timeout,
        "OpenAI",
    )
    data = _safe_json(raw, "OpenAI")
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise AIRefineError("OpenAI zwrócił pustą odpowiedź — spróbuj ponownie.")
    return _extract_variants(content)


def _call_anthropic(api_key: str, text: str, timeout: int) -> dict:
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": text}],
    }
    raw = _http_post(
        ANTHROPIC_ENDPOINT,
        {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        },
        payload,
        timeout,
        "Anthropic Claude",
    )
    data = _safe_json(raw, "Anthropic")
    try:
        content = data["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise AIRefineError("Anthropic zwrócił pustą odpowiedź — spróbuj ponownie.")
    return _extract_variants(content)


def _safe_json(raw: str, provider: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise AIRefineError(f"{provider}: nieprawidłowa odpowiedź API: {e}")


def _extract_variants(text: str) -> dict:
    """Parse the model's text payload, which should be a JSON object with three keys."""
    candidate = text.strip()
    try:
        variants = json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if not match:
            raise AIRefineError(f"Model zwrócił tekst niebędący JSON-em:\n{candidate[:300]}")
        try:
            variants = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise AIRefineError(f"Nie udało się sparsować JSON-a z odpowiedzi: {e}")

    if not isinstance(variants, dict):
        raise AIRefineError(f"Oczekiwano obiektu JSON, otrzymano: {type(variants).__name__}")

    result = {}
    for key in VARIANT_KEYS:
        value = variants.get(key)
        if not value or not isinstance(value, str):
            raise AIRefineError(f"Brak wariantu „{key}” w odpowiedzi modelu.")
        result[key] = value.strip()
    return result
