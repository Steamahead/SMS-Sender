import csv
import os

import phonenumbers
from openpyxl import load_workbook


def normalize_phone_number(raw) -> str:
    """Normalize a phone number to +48XXXXXXXXX format."""
    text = str(raw).strip().replace(" ", "").replace("-", "")

    if not text.startswith("+"):
        if text.startswith("48") and len(text) == 11:
            text = "+" + text
        elif len(text) == 9 and text.isdigit():
            text = "+48" + text
        else:
            text = "+" + text

    return text


def validate_phone_number(raw) -> tuple[bool, str | None, str | None]:
    """Validate and normalize a phone number.

    Returns: (is_valid, normalized_number_or_None, error_reason_or_None)
    """
    if raw is None or str(raw).strip() == "":
        return False, None, "Pusty numer"

    try:
        normalized = normalize_phone_number(raw)
        parsed = phonenumbers.parse(normalized, "PL")

        if not phonenumbers.is_valid_number(parsed):
            return False, None, f"Nieprawidlowy numer: {raw}"

        formatted = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
        return True, formatted, None

    except phonenumbers.NumberParseException:
        return False, None, f"Nie mozna sparsowac: {raw}"


def import_from_excel(path: str) -> tuple[list[str], list[dict]]:
    """Import phone numbers from .xlsx file (column A).

    Returns: (valid_numbers, skipped_entries)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    wb = load_workbook(path, read_only=True)
    ws = wb.active

    valid = []
    skipped = []

    for row_idx, row in enumerate(ws.iter_rows(min_col=1, max_col=1, values_only=True), start=1):
        raw = row[0]
        if raw is None or str(raw).strip() == "":
            skipped.append({"row": row_idx, "value": "", "reason": "Pusty numer"})
            continue

        is_valid, normalized, reason = validate_phone_number(raw)
        if is_valid:
            valid.append(normalized)
        else:
            skipped.append({"row": row_idx, "value": str(raw), "reason": reason})

    wb.close()
    return valid, skipped


def import_from_csv(path: str) -> tuple[list[str], list[dict]]:
    """Import phone numbers from .csv file (first column).

    Returns: (valid_numbers, skipped_entries)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    valid = []
    skipped = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row_idx, row in enumerate(reader, start=1):
            if not row or not row[0].strip():
                skipped.append({"row": row_idx, "value": "", "reason": "Pusty numer"})
                continue

            raw = row[0].strip()
            is_valid, normalized, reason = validate_phone_number(raw)
            if is_valid:
                valid.append(normalized)
            else:
                skipped.append({"row": row_idx, "value": raw, "reason": reason})

    return valid, skipped
