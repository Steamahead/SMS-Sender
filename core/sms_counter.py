"""How many SMS parts a message costs.

A single SMS holds 160 GSM-7 characters. One character outside the GSM-7
alphabet — any Polish letter (ą, ę, ś…) — switches the whole message to UCS-2,
which holds only 70. A message longer than one part is split, and every part
loses a few characters to the header that glues them back together:
153 per part for GSM-7, 67 for UCS-2.
"""
from dataclasses import dataclass

MAX_CHARS = 700

_GSM_BASIC = set(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
# Reachable through an escape code, so each one takes two slots.
_GSM_EXTENDED = set("^{}\\[~]|€\f")


# Polish letters plus the typographic marks Word and AI assistants like to
# insert — any one of them alone would switch the message to UCS-2.
_PLAIN = str.maketrans({
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o", "ś": "s", "ź": "z", "ż": "z",
    "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N", "Ó": "O", "Ś": "S", "Ź": "Z", "Ż": "Z",
    "„": '"', "”": '"', "“": '"', "«": '"', "»": '"',
    "‘": "'", "’": "'", "‚": "'",
    "–": "-", "—": "-", "…": "...", " ": " ",
})


def strip_polish(text: str) -> str:
    """Rewrite text into the GSM-7 alphabet: 160 characters per SMS instead of 70."""
    return text.translate(_PLAIN)


@dataclass(frozen=True)
class SmsCount:
    encoding: str  # "GSM" or "UCS-2"
    units: int     # slots used: GSM-7 septets or UCS-2 code units
    parts: int


def count_sms(text: str) -> SmsCount:
    if all(ch in _GSM_BASIC or ch in _GSM_EXTENDED for ch in text):
        units = sum(2 if ch in _GSM_EXTENDED else 1 for ch in text)
        single, multi, encoding = 160, 153, "GSM"
    else:
        # Characters outside the Basic Multilingual Plane (most emoji) take
        # two UTF-16 code units.
        units = len(text.encode("utf-16-le")) // 2
        single, multi, encoding = 70, 67, "UCS-2"

    if units == 0:
        parts = 0
    elif units <= single:
        parts = 1
    else:
        parts = -(-units // multi)
    return SmsCount(encoding=encoding, units=units, parts=parts)
