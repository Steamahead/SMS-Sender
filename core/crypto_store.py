"""Encrypt secrets at rest using Windows DPAPI (per-user scope).

Used for the API key so it is never stored as plaintext in settings.json.
Encrypted values are stored as ``dpapi:<base64>``. Values without that marker
are treated as plaintext (backward compatibility / migration). When DPAPI is
unavailable (e.g. non-Windows test runner) the functions degrade gracefully:
``protect`` returns the plaintext unchanged so the app keeps working.
"""
import base64

_MARKER = "dpapi:"
_DESCRIPTION = "SMSSender API key"

try:
    import win32crypt  # provided by pywin32 (pulled in by pywinauto)
    _DPAPI = True
except Exception:
    _DPAPI = False


def is_available() -> bool:
    """True when DPAPI encryption can be used on this machine."""
    return _DPAPI


def is_protected(stored: str) -> bool:
    """True when the stored value is an encrypted blob (not plaintext)."""
    return bool(stored) and stored.startswith(_MARKER)


def protect(plaintext: str) -> str:
    """Encrypt `plaintext` with DPAPI. Returns ``dpapi:<base64>``.

    Empty input or missing DPAPI returns the input unchanged."""
    if not plaintext or not _DPAPI:
        return plaintext
    blob = win32crypt.CryptProtectData(
        plaintext.encode("utf-8"), _DESCRIPTION, None, None, None, 0
    )
    return _MARKER + base64.b64encode(blob).decode("ascii")


def unprotect(stored: str) -> str:
    """Reverse :func:`protect`. Unmarked (plaintext) values pass through.

    Returns "" if a marked blob cannot be decrypted on this machine."""
    if not is_protected(stored):
        return stored
    if not _DPAPI:
        return ""
    try:
        blob = base64.b64decode(stored[len(_MARKER):])
        _, data = win32crypt.CryptUnprotectData(blob, None, None, None, 0)
        return data.decode("utf-8")
    except Exception:
        return ""
