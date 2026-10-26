from core.excel_importer import extract_phone_numbers


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
    - Wiersze oddzielone tabulatorami (kopiowanie z Excela) — bierze numery
      ze wszystkich komorek
    - Kilka numerow w jednej komorce: oddzielone przecinkiem, srednikiem albo
      nowa linia (Alt+Enter — Excel otacza wtedy komorke cudzyslowem)
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

        found_in_line = False

        for cell in line.split("\t"):
            numbers, bad = extract_phone_numbers(cell)
            valid.extend(numbers)
            found_in_line = found_in_line or bool(numbers)
            for fragment, reason in bad:
                skipped.append({"row": line_idx, "value": fragment, "reason": reason})

        if not found_in_line and not any(s["row"] == line_idx for s in skipped):
            skipped.append({
                "row": line_idx,
                "value": line,
                "reason": "Nie znaleziono numeru telefonu",
            })

    unique, _ = _deduplicate(valid)
    return unique, skipped
