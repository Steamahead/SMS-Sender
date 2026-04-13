from core.excel_importer import validate_phone_number


def _deduplicate(numbers):
    seen = set()
    unique = []
    for num in numbers:
        if num not in seen:
            seen.add(num)
            unique.append(num)
    return unique, len(numbers) - len(unique)


def parse_clipboard_text(text: str) -> tuple[list[str], list[dict]]:
    """Parsuje tekst ze schowka (kopiowanie z Excela lub zwykly tekst) na numery telefonow.

    Obsluguje:
    - Jeden numer w linii
    - Wiersze oddzielone tabulatorami (kopiowanie z Excela) — sprawdza kazda komorke
    - Dodatkowe biale znaki

    Zwraca: (unikalne_poprawne_numery, pominiete_wpisy)
    """
    if not text or not text.strip():
        return [], []

    valid = []
    skipped = []
    lines = text.strip().split("\n")

    for line_idx, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        cells = line.split("\t") if "\t" in line else [line]
        found_in_line = False

        for cell in cells:
            cell = cell.strip()
            if not cell:
                continue
            is_valid, normalized, reason = validate_phone_number(cell)
            if is_valid:
                valid.append(normalized)
                found_in_line = True
                break

        if not found_in_line:
            skipped.append({
                "row": line_idx,
                "value": line,
                "reason": "Nie znaleziono numeru telefonu",
            })

    unique, _ = _deduplicate(valid)
    return unique, skipped
