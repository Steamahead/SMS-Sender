import csv
import io
import os
import re

import phonenumbers
from openpyxl import load_workbook


def normalize_phone_number(raw) -> str:
    """Normalize a phone number to +48XXXXXXXXX format."""
    text = str(raw).strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")

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


# Separators people put between several numbers in one cell. Spaces and dashes
# are not among them: they appear *inside* a number ("512 345 678").
_CELL_SEPARATORS = re.compile(r"[,;|\r\n]+")
_LOOKS_LIKE_NUMBER = re.compile(r"^[\d\s+\-().]+$")


def extract_phone_numbers(raw) -> tuple[list[str], list[tuple[str, str]]]:
    """All phone numbers in one cell, e.g. "512 345 678; 600-700-800".

    Returns (valid_normalized_numbers, [(bad_fragment, reason), ...]). Only
    fragments that look like a number count as bad — "Anna" in a pasted row is
    a name, not a typo in a phone number.
    """
    if raw is None:
        return [], []
    valid, bad = [], []
    for fragment in _CELL_SEPARATORS.split(str(raw)):
        fragment = fragment.strip().strip('"').strip()
        if not fragment:
            continue
        is_valid, normalized, reason = validate_phone_number(fragment)
        if is_valid:
            valid.append(normalized)
        elif _LOOKS_LIKE_NUMBER.match(fragment):
            bad.append((fragment, reason))
    return valid, bad


def _collect_cell(raw, row_idx: int, row: list, valid: list, skipped: list,
                  row_data: list | None) -> None:
    """Add every number from one phone cell; each one carries a copy of its row,
    so "{Imie}" still resolves for all numbers of a "512…; 600…" cell."""
    numbers, bad = extract_phone_numbers(raw)
    for number in numbers:
        valid.append(number)
        if row_data is not None:
            row_data.append(list(row))
    for fragment, reason in bad:
        skipped.append({"row": row_idx, "value": fragment, "reason": reason})
    if not numbers and not bad:
        _, _, reason = validate_phone_number(raw)
        skipped.append({"row": row_idx, "value": str(raw), "reason": reason})


def detect_phone_column(path: str, max_rows: int = 50) -> int | None:
    """Auto-detect which column contains phone numbers.
    Scans up to max_rows rows, returns 0-based column index with most valid numbers.
    Returns None if no column has at least 2 valid numbers.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    wb = load_workbook(path, read_only=True)
    ws = wb.active

    scores: dict[int, int] = {}

    for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if row_idx > max_rows:
            break
        for col_idx, val in enumerate(row):
            if val is None or str(val).strip() == "":
                continue
            is_valid, _, _ = validate_phone_number(val)
            if is_valid:
                scores[col_idx] = scores.get(col_idx, 0) + 1

    wb.close()

    if not scores:
        return None

    best_col = max(scores, key=scores.get)
    if scores[best_col] < 2:
        return None
    return best_col


def import_from_excel(
    path: str,
    column: int = 0,
    return_rows: bool = False,
) -> tuple[list[str], list[dict]] | tuple[list[str], list[dict], list[list]]:
    """Import phone numbers from .xlsx file.

    Args:
        path: Path to .xlsx file
        column: 0-based column index to read phone numbers from
        return_rows: If True, also return all row data (for personalization)

    Returns: (valid_numbers, skipped_entries) or (valid_numbers, skipped_entries, row_data)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    wb = load_workbook(path, read_only=True)
    ws = wb.active

    valid = []
    skipped = []
    row_data = []

    for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
        row_list = list(row)

        if column >= len(row_list):
            skipped.append({"row": row_idx, "value": "", "reason": "Brak kolumny"})
            continue

        raw = row_list[column]
        if raw is None or str(raw).strip() == "":
            skipped.append({"row": row_idx, "value": "", "reason": "Pusty numer"})
            continue

        _collect_cell(
            raw, row_idx, [str(v) if v is not None else "" for v in row_list],
            valid, skipped, row_data if return_rows else None,
        )

    wb.close()

    if return_rows:
        return valid, skipped, row_data
    return valid, skipped


def deduplicate_numbers(numbers: list[str]) -> tuple[list[str], int]:
    """Remove duplicate phone numbers preserving order.
    Returns: (unique_numbers, count_of_removed_duplicates)
    """
    seen = set()
    unique = []
    for num in numbers:
        if num not in seen:
            seen.add(num)
            unique.append(num)
    return unique, len(numbers) - len(unique)


def deduplicate_with_rows(
    numbers: list[str], rows: list[list],
) -> tuple[list[str], list[list], int]:
    """Like deduplicate_numbers, but drops each duplicate's data row too.

    ``rows[i]`` belongs to ``numbers[i]``. Removing a number without its row
    shifts every later row by one, and personalized SMS-es go out with the
    previous person's name.
    """
    seen = set()
    unique, unique_rows = [], []
    for i, num in enumerate(numbers):
        if num in seen:
            continue
        seen.add(num)
        unique.append(num)
        if i < len(rows):
            unique_rows.append(rows[i])
    return unique, unique_rows, len(numbers) - len(unique)


def get_column_headers(path: str) -> list[str] | None:
    """Read first row of Excel file and return as headers if they look like text.
    Returns None if the first row looks like data (contains valid phone numbers).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    wb = load_workbook(path, read_only=True)
    ws = wb.active

    first_row = []
    for row in ws.iter_rows(max_row=1, values_only=True):
        first_row = [str(v) if v is not None else "" for v in row]
        break

    wb.close()
    return _headers_from_first_row(first_row)


def _headers_from_first_row(first_row: list[str]) -> list[str] | None:
    """The first row is a header unless it already holds a phone number."""
    if not first_row:
        return None

    phone_count = sum(
        1 for val in first_row
        if val.strip() and validate_phone_number(val)[0]
    )

    if phone_count > 0:
        return None

    return first_row


def read_csv_rows(path: str) -> list[list[str]]:
    """Read a CSV the way Polish users actually produce it.

    Excel with Polish regional settings saves ";"-separated files in cp1250
    (or UTF-8 with a BOM for "CSV UTF-8"); other tools write ","-separated
    UTF-8. Decode with the first encoding that fits and split on whichever
    separator the header line uses most.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    with open(path, "rb") as f:
        raw = f.read()
    for encoding in ("utf-8-sig", "cp1250"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")

    first_line = text.split("\n", 1)[0]
    delimiter = max((";", ",", "\t"), key=first_line.count)
    if first_line.count(delimiter) == 0:
        delimiter = ","
    return list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))


def get_column_headers_csv(path: str) -> list[str] | None:
    """CSV counterpart of get_column_headers."""
    rows = read_csv_rows(path)
    return _headers_from_first_row(rows[0] if rows else [])


def detect_phone_column_csv(path: str, max_rows: int = 50) -> int | None:
    """Auto-detect which column in a CSV contains phone numbers."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    scores: dict[int, int] = {}

    for row in read_csv_rows(path)[:max_rows]:
        for col_idx, val in enumerate(row):
            if not val.strip():
                continue
            is_valid, _, _ = validate_phone_number(val)
            if is_valid:
                scores[col_idx] = scores.get(col_idx, 0) + 1

    if not scores:
        return None

    best_col = max(scores, key=scores.get)
    if scores[best_col] < 2:
        return None
    return best_col


def import_from_csv(
    path: str,
    column: int = 0,
    return_rows: bool = False,
) -> tuple[list[str], list[dict]] | tuple[list[str], list[dict], list[list]]:
    """Import phone numbers from .csv file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    valid = []
    skipped = []
    row_data = []

    for row_idx, row in enumerate(read_csv_rows(path), start=1):
        if column >= len(row) or not row[column].strip():
            skipped.append({"row": row_idx, "value": "", "reason": "Pusty numer"})
            continue

        _collect_cell(
            row[column].strip(), row_idx, row,
            valid, skipped, row_data if return_rows else None,
        )

    if return_rows:
        return valid, skipped, row_data
    return valid, skipped
