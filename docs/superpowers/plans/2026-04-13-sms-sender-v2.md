# SMS Sender v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild SMS Sender with PySide6 UI, add column auto-detection, drag&drop, clipboard paste, message personalization, templates, history, reports, deduplication, and package as Windows installer.

**Architecture:** Core modules (excel_importer, batch_manager, sender) get extended with new modules (personalizer, template_manager, history, report, settings). GUI is rewritten from tkinter to PySide6 with widget decomposition. Automation layer (phone_link.py) stays unchanged. PyInstaller + Inno Setup for distribution.

**Tech Stack:** Python 3.11+, PySide6, openpyxl, pywinauto, phonenumbers, SQLite (stdlib), PyInstaller, Inno Setup

---

### Task 1: Update dependencies and project setup

**Files:**
- Modify: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Update requirements.txt**

```
openpyxl>=3.1.0
pywinauto>=0.6.8
phonenumbers>=8.13.0
PySide6>=6.6.0
pyinstaller>=6.0.0
```

- [ ] **Step 2: Install new dependencies**

Run: `pip install PySide6 pyinstaller`
Expected: Successfully installed

- [ ] **Step 3: Verify PySide6 import**

Run: `python -c "from PySide6.QtWidgets import QApplication; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add PySide6 and PyInstaller dependencies"
```

---

### Task 2: Column auto-detection in excel_importer

**Files:**
- Modify: `core/excel_importer.py`
- Create: `tests/test_column_detection.py`

- [ ] **Step 1: Write failing tests for detect_phone_column**

```python
# tests/test_column_detection.py
import os
import tempfile

import pytest
from openpyxl import Workbook

from core.excel_importer import detect_phone_column


class TestDetectPhoneColumn:
    def _create_xlsx(self, rows: list[list]) -> str:
        wb = Workbook()
        ws = wb.active
        for r_idx, row in enumerate(rows, start=1):
            for c_idx, val in enumerate(row, start=1):
                ws.cell(row=r_idx, column=c_idx, value=val)
        path = os.path.join(tempfile.mkdtemp(), "test.xlsx")
        wb.save(path)
        return path

    def test_phone_in_column_a(self):
        path = self._create_xlsx([
            ["+48512345678", "Jan", "Kowalski"],
            ["601234567", "Anna", "Nowak"],
            ["48701234567", "Piotr", "Wisniewski"],
        ])
        assert detect_phone_column(path) == 0

    def test_phone_in_column_b(self):
        path = self._create_xlsx([
            ["Jan", "+48512345678", "Firma A"],
            ["Anna", "601234567", "Firma B"],
            ["Piotr", "48701234567", "Firma C"],
        ])
        assert detect_phone_column(path) == 1

    def test_phone_in_column_c(self):
        path = self._create_xlsx([
            ["Jan", "Kowalski", "512345678"],
            ["Anna", "Nowak", "601234567"],
        ])
        assert detect_phone_column(path) == 2

    def test_no_phone_column(self):
        path = self._create_xlsx([
            ["Jan", "Kowalski", "Firma"],
            ["Anna", "Nowak", "Firma B"],
        ])
        assert detect_phone_column(path) is None

    def test_empty_file(self):
        path = self._create_xlsx([])
        assert detect_phone_column(path) is None

    def test_mixed_data_picks_best_column(self):
        path = self._create_xlsx([
            ["12345", "+48512345678", "text"],
            ["abc", "601234567", "text"],
            ["xyz", "48701234567", "text"],
        ])
        assert detect_phone_column(path) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_column_detection.py -v`
Expected: FAIL — `ImportError: cannot import name 'detect_phone_column'`

- [ ] **Step 3: Implement detect_phone_column**

Add to `core/excel_importer.py` after the `validate_phone_number` function:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_column_detection.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Write failing tests for import_from_excel with column parameter**

Add to `tests/test_column_detection.py`:

```python
from core.excel_importer import import_from_excel


class TestImportWithColumn:
    def _create_xlsx(self, rows: list[list]) -> str:
        wb = Workbook()
        ws = wb.active
        for r_idx, row in enumerate(rows, start=1):
            for c_idx, val in enumerate(row, start=1):
                ws.cell(row=r_idx, column=c_idx, value=val)
        path = os.path.join(tempfile.mkdtemp(), "test.xlsx")
        wb.save(path)
        return path

    def test_import_from_column_b(self):
        path = self._create_xlsx([
            ["Jan", "+48512345678"],
            ["Anna", "601234567"],
        ])
        valid, skipped = import_from_excel(path, column=1)
        assert len(valid) == 2

    def test_import_default_column_a(self):
        path = self._create_xlsx([
            ["+48512345678"],
            ["601234567"],
        ])
        valid, skipped = import_from_excel(path, column=0)
        assert len(valid) == 2

    def test_import_returns_all_row_data(self):
        path = self._create_xlsx([
            ["Jan", "+48512345678", "Firma A"],
            ["Anna", "601234567", "Firma B"],
        ])
        valid, skipped, row_data = import_from_excel(path, column=1, return_rows=True)
        assert len(valid) == 2
        assert row_data[0] == ["Jan", "+48512345678", "Firma A"]
        assert row_data[1] == ["Anna", "601234567", "Firma B"]
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `pytest tests/test_column_detection.py::TestImportWithColumn -v`
Expected: FAIL — `TypeError: import_from_excel() got an unexpected keyword argument 'column'`

- [ ] **Step 7: Update import_from_excel to accept column and return_rows**

Replace the `import_from_excel` function in `core/excel_importer.py`:

```python
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

        is_valid, normalized, reason = validate_phone_number(raw)
        if is_valid:
            valid.append(normalized)
            if return_rows:
                row_data.append([str(v) if v is not None else "" for v in row_list])
        else:
            skipped.append({"row": row_idx, "value": str(raw), "reason": reason})

    wb.close()

    if return_rows:
        return valid, skipped, row_data
    return valid, skipped
```

- [ ] **Step 8: Run all importer tests**

Run: `pytest tests/test_column_detection.py tests/test_excel_importer.py -v`
Expected: All tests PASS (existing tests still work with default `column=0`)

- [ ] **Step 9: Add detect_phone_column_csv and update import_from_csv with column param**

Add to `core/excel_importer.py`:

```python
def detect_phone_column_csv(path: str, max_rows: int = 50) -> int | None:
    """Auto-detect which column in a CSV contains phone numbers."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    scores: dict[int, int] = {}

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row_idx, row in enumerate(reader, start=1):
            if row_idx > max_rows:
                break
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
    """Import phone numbers from .csv file.

    Args:
        path: Path to .csv file
        column: 0-based column index to read phone numbers from
        return_rows: If True, also return all row data (for personalization)

    Returns: (valid_numbers, skipped_entries) or (valid_numbers, skipped_entries, row_data)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    valid = []
    skipped = []
    row_data = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row_idx, row in enumerate(reader, start=1):
            if column >= len(row) or not row[column].strip():
                skipped.append({"row": row_idx, "value": "", "reason": "Pusty numer"})
                continue

            raw = row[column].strip()
            is_valid, normalized, reason = validate_phone_number(raw)
            if is_valid:
                valid.append(normalized)
                if return_rows:
                    row_data.append(row)
            else:
                skipped.append({"row": row_idx, "value": raw, "reason": reason})

    if return_rows:
        return valid, skipped, row_data
    return valid, skipped
```

- [ ] **Step 10: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 11: Commit**

```bash
git add core/excel_importer.py tests/test_column_detection.py
git commit -m "feat: add column auto-detection and configurable column import"
```

---

### Task 3: Deduplication and header detection

**Files:**
- Modify: `core/excel_importer.py`
- Create: `tests/test_deduplication.py`

- [ ] **Step 1: Write failing tests for deduplicate_numbers**

```python
# tests/test_deduplication.py
from core.excel_importer import deduplicate_numbers


class TestDeduplicateNumbers:
    def test_no_duplicates(self):
        numbers = ["+48512345678", "+48601234567"]
        unique, removed = deduplicate_numbers(numbers)
        assert unique == ["+48512345678", "+48601234567"]
        assert removed == 0

    def test_with_duplicates(self):
        numbers = ["+48512345678", "+48601234567", "+48512345678"]
        unique, removed = deduplicate_numbers(numbers)
        assert unique == ["+48512345678", "+48601234567"]
        assert removed == 1

    def test_all_duplicates(self):
        numbers = ["+48512345678", "+48512345678", "+48512345678"]
        unique, removed = deduplicate_numbers(numbers)
        assert unique == ["+48512345678"]
        assert removed == 2

    def test_empty_list(self):
        unique, removed = deduplicate_numbers([])
        assert unique == []
        assert removed == 0

    def test_preserves_order(self):
        numbers = ["+48701234567", "+48512345678", "+48601234567", "+48512345678"]
        unique, removed = deduplicate_numbers(numbers)
        assert unique == ["+48701234567", "+48512345678", "+48601234567"]
        assert removed == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_deduplication.py -v`
Expected: FAIL — `ImportError: cannot import name 'deduplicate_numbers'`

- [ ] **Step 3: Implement deduplicate_numbers**

Add to `core/excel_importer.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_deduplication.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Write tests for get_column_headers**

Add to `tests/test_column_detection.py`:

```python
from core.excel_importer import get_column_headers


class TestGetColumnHeaders:
    def _create_xlsx(self, rows: list[list]) -> str:
        wb = Workbook()
        ws = wb.active
        for r_idx, row in enumerate(rows, start=1):
            for c_idx, val in enumerate(row, start=1):
                ws.cell(row=r_idx, column=c_idx, value=val)
        path = os.path.join(tempfile.mkdtemp(), "test.xlsx")
        wb.save(path)
        return path

    def test_has_headers(self):
        path = self._create_xlsx([
            ["Imie", "Telefon", "Firma"],
            ["Jan", "+48512345678", "ABC"],
        ])
        headers = get_column_headers(path)
        assert headers == ["Imie", "Telefon", "Firma"]

    def test_numeric_first_row_no_headers(self):
        path = self._create_xlsx([
            ["+48512345678", "601234567"],
            ["+48701234567", "501234567"],
        ])
        headers = get_column_headers(path)
        assert headers is None

    def test_empty_file(self):
        path = self._create_xlsx([])
        headers = get_column_headers(path)
        assert headers is None
```

- [ ] **Step 6: Implement get_column_headers**

Add to `core/excel_importer.py`:

```python
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

    if not first_row:
        return None

    phone_count = sum(
        1 for val in first_row
        if val.strip() and validate_phone_number(val)[0]
    )

    if phone_count > 0:
        return None

    return first_row
```

- [ ] **Step 7: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add core/excel_importer.py tests/test_deduplication.py tests/test_column_detection.py
git commit -m "feat: add number deduplication and column header detection"
```

---

### Task 4: Clipboard import (parse_clipboard_numbers)

**Files:**
- Create: `core/clipboard_import.py`
- Create: `tests/test_clipboard_import.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_clipboard_import.py
from core.clipboard_import import parse_clipboard_text


class TestParseClipboardText:
    def test_one_number_per_line(self):
        text = "+48512345678\n601234567\n48701234567"
        valid, skipped = parse_clipboard_text(text)
        assert len(valid) == 3
        assert all(n.startswith("+48") for n in valid)

    def test_tab_separated_excel_format(self):
        text = "Jan\t+48512345678\tFirma A\nAnna\t601234567\tFirma B"
        valid, skipped = parse_clipboard_text(text)
        assert len(valid) == 2

    def test_mixed_valid_invalid(self):
        text = "+48512345678\nabc\n601234567"
        valid, skipped = parse_clipboard_text(text)
        assert len(valid) == 2
        assert len(skipped) == 1

    def test_empty_text(self):
        valid, skipped = parse_clipboard_text("")
        assert len(valid) == 0
        assert len(skipped) == 0

    def test_with_extra_whitespace(self):
        text = "  +48512345678  \n  601234567  \n"
        valid, skipped = parse_clipboard_text(text)
        assert len(valid) == 2

    def test_deduplicates(self):
        text = "+48512345678\n512345678\n+48512345678"
        valid, skipped = parse_clipboard_text(text)
        assert len(valid) == 1

    def test_single_column_pasted(self):
        text = "512345678\n601234567\n701234567"
        valid, skipped = parse_clipboard_text(text)
        assert len(valid) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_clipboard_import.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.clipboard_import'`

- [ ] **Step 3: Implement parse_clipboard_text**

```python
# core/clipboard_import.py
from core.excel_importer import validate_phone_number, deduplicate_numbers


def parse_clipboard_text(text: str) -> tuple[list[str], list[dict]]:
    """Parse clipboard text (from Excel copy or plain text) into phone numbers.

    Handles:
    - One number per line
    - Tab-separated rows (Excel copy) — tries each cell
    - Extra whitespace

    Returns: (valid_numbers_deduplicated, skipped_entries)
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

    unique, _ = deduplicate_numbers(valid)
    return unique, skipped
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_clipboard_import.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/clipboard_import.py tests/test_clipboard_import.py
git commit -m "feat: add clipboard text parser for Ctrl+V import"
```

---

### Task 5: Message personalizer

**Files:**
- Create: `core/personalizer.py`
- Create: `tests/test_personalizer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_personalizer.py
from core.personalizer import Personalizer


class TestPersonalizer:
    def test_simple_variable(self):
        p = Personalizer(
            template="Witaj {Imie}, zapraszamy!",
            headers=["Imie", "Telefon", "Firma"],
        )
        result = p.render(["Jan", "+48512345678", "ABC"])
        assert result == "Witaj Jan, zapraszamy!"

    def test_multiple_variables(self):
        p = Personalizer(
            template="Witaj {Imie} z {Firma}!",
            headers=["Imie", "Telefon", "Firma"],
        )
        result = p.render(["Jan", "+48512345678", "TechCorp"])
        assert result == "Witaj Jan z TechCorp!"

    def test_no_variables(self):
        p = Personalizer(
            template="Przypominamy o spotkaniu",
            headers=["Imie"],
        )
        result = p.render(["Jan"])
        assert result == "Przypominamy o spotkaniu"

    def test_missing_variable_value_empty(self):
        p = Personalizer(
            template="Witaj {Imie}!",
            headers=["Imie", "Telefon"],
        )
        result = p.render(["", "+48512345678"])
        assert result == "Witaj !"

    def test_letter_based_variables_no_headers(self):
        p = Personalizer(
            template="Witaj {A}, firma {C}!",
            headers=None,
        )
        result = p.render(["Jan", "+48512345678", "ABC"])
        assert result == "Witaj Jan, firma ABC!"

    def test_extract_variables(self):
        p = Personalizer(
            template="Witaj {Imie} z {Firma}!",
            headers=["Imie", "Telefon", "Firma"],
        )
        assert p.variables == ["Imie", "Firma"]

    def test_validate_all_variables_mapped(self):
        p = Personalizer(
            template="Witaj {Imie} z {NieIstniejaca}!",
            headers=["Imie", "Telefon"],
        )
        missing = p.missing_variables()
        assert missing == ["NieIstniejaca"]

    def test_validate_ok(self):
        p = Personalizer(
            template="Witaj {Imie}!",
            headers=["Imie", "Telefon"],
        )
        assert p.missing_variables() == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_personalizer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.personalizer'`

- [ ] **Step 3: Implement Personalizer**

```python
# core/personalizer.py
import re


class Personalizer:
    """Substitutes {variable} placeholders in SMS templates with row data."""

    _VAR_RE = re.compile(r"\{(\w+)\}")

    def __init__(self, template: str, headers: list[str] | None):
        self._template = template
        self._headers = headers
        self._variables = self._VAR_RE.findall(template)

    @property
    def variables(self) -> list[str]:
        return self._variables

    def missing_variables(self) -> list[str]:
        """Return list of variables that cannot be mapped to columns."""
        available = self._available_names()
        return [v for v in self._variables if v not in available]

    def render(self, row: list[str]) -> str:
        """Substitute variables in template with values from row data."""
        mapping = self._build_mapping(row)

        def replacer(match):
            name = match.group(1)
            return mapping.get(name, match.group(0))

        return self._VAR_RE.sub(replacer, self._template)

    def _available_names(self) -> set[str]:
        names = set()
        if self._headers:
            names.update(self._headers)
        # Always allow letter-based: A, B, C...
        for i in range(26):
            names.add(chr(65 + i))
        return names

    def _build_mapping(self, row: list[str]) -> dict[str, str]:
        mapping = {}
        # Letter-based mapping: A=0, B=1, C=2...
        for i, val in enumerate(row):
            if i < 26:
                mapping[chr(65 + i)] = val

        # Header-based mapping
        if self._headers:
            for i, header in enumerate(self._headers):
                if i < len(row):
                    mapping[header] = row[i]

        return mapping
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_personalizer.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/personalizer.py tests/test_personalizer.py
git commit -m "feat: add message personalizer with variable substitution"
```

---

### Task 6: Template manager

**Files:**
- Create: `core/template_manager.py`
- Create: `tests/test_template_manager.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_template_manager.py
import os
import tempfile
import json

import pytest

from core.template_manager import TemplateManager


class TestTemplateManager:
    def _make_manager(self) -> TemplateManager:
        path = os.path.join(tempfile.mkdtemp(), "templates.json")
        return TemplateManager(path)

    def test_save_and_list(self):
        tm = self._make_manager()
        tm.save("powitanie", "Witaj {Imie}!")
        assert tm.list_names() == ["powitanie"]

    def test_load(self):
        tm = self._make_manager()
        tm.save("powitanie", "Witaj {Imie}!")
        assert tm.load("powitanie") == "Witaj {Imie}!"

    def test_load_nonexistent(self):
        tm = self._make_manager()
        assert tm.load("nie_istnieje") is None

    def test_delete(self):
        tm = self._make_manager()
        tm.save("powitanie", "Witaj!")
        tm.delete("powitanie")
        assert tm.list_names() == []

    def test_delete_nonexistent_no_error(self):
        tm = self._make_manager()
        tm.delete("nie_istnieje")

    def test_overwrite(self):
        tm = self._make_manager()
        tm.save("powitanie", "v1")
        tm.save("powitanie", "v2")
        assert tm.load("powitanie") == "v2"
        assert len(tm.list_names()) == 1

    def test_persistence(self):
        path = os.path.join(tempfile.mkdtemp(), "templates.json")
        tm1 = TemplateManager(path)
        tm1.save("powitanie", "Witaj!")

        tm2 = TemplateManager(path)
        assert tm2.load("powitanie") == "Witaj!"

    def test_multiple_templates(self):
        tm = self._make_manager()
        tm.save("powitanie", "Witaj!")
        tm.save("przypomnienie", "Przypominamy...")
        names = tm.list_names()
        assert "powitanie" in names
        assert "przypomnienie" in names
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_template_manager.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement TemplateManager**

```python
# core/template_manager.py
import json
import os


class TemplateManager:
    """Manages saved SMS templates as a JSON file."""

    def __init__(self, path: str):
        self._path = path
        self._templates: dict[str, str] = {}
        self._load_from_disk()

    def save(self, name: str, content: str) -> None:
        self._templates[name] = content
        self._save_to_disk()

    def load(self, name: str) -> str | None:
        return self._templates.get(name)

    def delete(self, name: str) -> None:
        self._templates.pop(name, None)
        self._save_to_disk()

    def list_names(self) -> list[str]:
        return sorted(self._templates.keys())

    def _load_from_disk(self) -> None:
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                self._templates = json.load(f)

    def _save_to_disk(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._templates, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_template_manager.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/template_manager.py tests/test_template_manager.py
git commit -m "feat: add template manager for saving/loading SMS templates"
```

---

### Task 7: History module (SQLite)

**Files:**
- Create: `core/history.py`
- Create: `tests/test_history.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_history.py
import os
import tempfile

import pytest

from core.history import HistoryManager


class TestHistoryManager:
    def _make_manager(self) -> HistoryManager:
        path = os.path.join(tempfile.mkdtemp(), "history.db")
        return HistoryManager(path)

    def test_save_session(self):
        hm = self._make_manager()
        session_id = hm.save_session(
            message="Witaj!",
            source_file="dane.xlsx",
            recipients=[
                {"number": "+48512345678", "status": "sent", "error": None},
                {"number": "+48601234567", "status": "error", "error": "Timeout"},
            ],
        )
        assert session_id is not None

    def test_list_sessions(self):
        hm = self._make_manager()
        hm.save_session("Msg1", "f1.xlsx", [
            {"number": "+48512345678", "status": "sent", "error": None},
        ])
        hm.save_session("Msg2", "f2.xlsx", [
            {"number": "+48601234567", "status": "sent", "error": None},
        ])
        sessions = hm.list_sessions()
        assert len(sessions) == 2
        assert sessions[0]["message"] == "Msg2"  # newest first

    def test_get_session_details(self):
        hm = self._make_manager()
        sid = hm.save_session("Witaj!", "dane.xlsx", [
            {"number": "+48512345678", "status": "sent", "error": None},
            {"number": "+48601234567", "status": "error", "error": "Timeout"},
        ])
        details = hm.get_session(sid)
        assert details["message"] == "Witaj!"
        assert details["source_file"] == "dane.xlsx"
        assert len(details["recipients"]) == 2
        assert details["recipients"][0]["status"] == "sent"
        assert details["recipients"][1]["error"] == "Timeout"

    def test_summary_counts(self):
        hm = self._make_manager()
        sid = hm.save_session("Hi", "f.xlsx", [
            {"number": "+48512345678", "status": "sent", "error": None},
            {"number": "+48601234567", "status": "sent", "error": None},
            {"number": "+48701234567", "status": "error", "error": "Fail"},
        ])
        details = hm.get_session(sid)
        assert details["total"] == 3
        assert details["sent"] == 2
        assert details["errors"] == 1

    def test_max_sessions_limit(self):
        hm = self._make_manager()
        hm.MAX_SESSIONS = 3
        for i in range(5):
            hm.save_session(f"Msg{i}", f"f{i}.xlsx", [
                {"number": "+48512345678", "status": "sent", "error": None},
            ])
        sessions = hm.list_sessions()
        assert len(sessions) == 3

    def test_persistence(self):
        path = os.path.join(tempfile.mkdtemp(), "history.db")
        hm1 = HistoryManager(path)
        hm1.save_session("Witaj!", "f.xlsx", [
            {"number": "+48512345678", "status": "sent", "error": None},
        ])

        hm2 = HistoryManager(path)
        sessions = hm2.list_sessions()
        assert len(sessions) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_history.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement HistoryManager**

```python
# core/history.py
import os
import sqlite3
import json
from datetime import datetime


class HistoryManager:
    """Stores SMS sending history in SQLite."""

    MAX_SESSIONS = 1000

    def __init__(self, db_path: str):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    recipients_json TEXT NOT NULL
                )
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def save_session(
        self,
        message: str,
        source_file: str,
        recipients: list[dict],
    ) -> int:
        """Save a sending session. Returns session ID."""
        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO sessions (created_at, message, source_file, recipients_json) "
                "VALUES (?, ?, ?, ?)",
                (
                    datetime.now().isoformat(),
                    message,
                    source_file,
                    json.dumps(recipients, ensure_ascii=False),
                ),
            )
            session_id = cursor.lastrowid
            self._enforce_limit(conn)
            return session_id

    def list_sessions(self) -> list[dict]:
        """Return all sessions, newest first."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, created_at, message, source_file, recipients_json "
                "FROM sessions ORDER BY id DESC"
            ).fetchall()

        sessions = []
        for row in rows:
            recipients = json.loads(row[4])
            sessions.append({
                "id": row[0],
                "created_at": row[1],
                "message": row[2],
                "source_file": row[3],
                "total": len(recipients),
                "sent": sum(1 for r in recipients if r["status"] == "sent"),
                "errors": sum(1 for r in recipients if r["status"] == "error"),
            })
        return sessions

    def get_session(self, session_id: int) -> dict | None:
        """Return full session details including recipients."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, created_at, message, source_file, recipients_json "
                "FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

        if not row:
            return None

        recipients = json.loads(row[4])
        return {
            "id": row[0],
            "created_at": row[1],
            "message": row[2],
            "source_file": row[3],
            "recipients": recipients,
            "total": len(recipients),
            "sent": sum(1 for r in recipients if r["status"] == "sent"),
            "errors": sum(1 for r in recipients if r["status"] == "error"),
        }

    def _enforce_limit(self, conn: sqlite3.Connection) -> None:
        count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        if count > self.MAX_SESSIONS:
            excess = count - self.MAX_SESSIONS
            conn.execute(
                "DELETE FROM sessions WHERE id IN "
                "(SELECT id FROM sessions ORDER BY id ASC LIMIT ?)",
                (excess,),
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_history.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/history.py tests/test_history.py
git commit -m "feat: add SQLite-based sending history"
```

---

### Task 8: Report exporter

**Files:**
- Create: `core/report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_report.py
import os
import tempfile

import pytest
from openpyxl import load_workbook

from core.report import export_report_xlsx, export_report_csv


class TestExportReportXlsx:
    def test_creates_file(self):
        path = os.path.join(tempfile.mkdtemp(), "report.xlsx")
        recipients = [
            {"number": "+48512345678", "status": "sent", "message": "Witaj!", "time": "14:32:01", "error": ""},
            {"number": "+48601234567", "status": "error", "message": "Witaj!", "time": "14:32:05", "error": "Timeout"},
        ]
        export_report_xlsx(path, recipients)
        assert os.path.exists(path)

    def test_correct_content(self):
        path = os.path.join(tempfile.mkdtemp(), "report.xlsx")
        recipients = [
            {"number": "+48512345678", "status": "sent", "message": "Witaj!", "time": "14:32:01", "error": ""},
        ]
        export_report_xlsx(path, recipients)
        wb = load_workbook(path)
        ws = wb.active
        assert ws.cell(1, 1).value == "Numer"
        assert ws.cell(1, 2).value == "Status"
        assert ws.cell(2, 1).value == "+48512345678"
        assert ws.cell(2, 2).value == "sent"
        wb.close()

    def test_empty_recipients(self):
        path = os.path.join(tempfile.mkdtemp(), "report.xlsx")
        export_report_xlsx(path, [])
        assert os.path.exists(path)


class TestExportReportCsv:
    def test_creates_file(self):
        path = os.path.join(tempfile.mkdtemp(), "report.csv")
        recipients = [
            {"number": "+48512345678", "status": "sent", "message": "Witaj!", "time": "14:32:01", "error": ""},
        ]
        export_report_csv(path, recipients)
        assert os.path.exists(path)

    def test_correct_content(self):
        path = os.path.join(tempfile.mkdtemp(), "report.csv")
        recipients = [
            {"number": "+48512345678", "status": "sent", "message": "Witaj!", "time": "14:32:01", "error": ""},
        ]
        export_report_csv(path, recipients)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert "Numer" in lines[0]
        assert "+48512345678" in lines[1]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement report exporters**

```python
# core/report.py
import csv
import os

from openpyxl import Workbook


_HEADERS = ["Numer", "Status", "Tresc", "Czas", "Blad"]


def export_report_xlsx(path: str, recipients: list[dict]) -> None:
    """Export sending report to Excel file."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Raport SMS"

    for col_idx, header in enumerate(_HEADERS, start=1):
        ws.cell(row=1, column=col_idx, value=header)

    for row_idx, r in enumerate(recipients, start=2):
        ws.cell(row=row_idx, column=1, value=r.get("number", ""))
        ws.cell(row=row_idx, column=2, value=r.get("status", ""))
        ws.cell(row=row_idx, column=3, value=r.get("message", ""))
        ws.cell(row=row_idx, column=4, value=r.get("time", ""))
        ws.cell(row=row_idx, column=5, value=r.get("error", ""))

    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    wb.save(path)


def export_report_csv(path: str, recipients: list[dict]) -> None:
    """Export sending report to CSV file."""
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(_HEADERS)
        for r in recipients:
            writer.writerow([
                r.get("number", ""),
                r.get("status", ""),
                r.get("message", ""),
                r.get("time", ""),
                r.get("error", ""),
            ])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_report.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/report.py tests/test_report.py
git commit -m "feat: add report exporter (Excel and CSV)"
```

---

### Task 9: Settings manager

**Files:**
- Create: `core/settings.py`
- Create: `tests/test_settings.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_settings.py
import os
import tempfile

from core.settings import Settings


class TestSettings:
    def _make_settings(self) -> Settings:
        path = os.path.join(tempfile.mkdtemp(), "settings.json")
        return Settings(path)

    def test_default_values(self):
        s = self._make_settings()
        assert s.last_import_dir == ""
        assert s.batch_size == 20
        assert s.window_width == 900
        assert s.window_height == 700

    def test_set_and_get(self):
        s = self._make_settings()
        s.last_import_dir = "C:/Users/dane"
        assert s.last_import_dir == "C:/Users/dane"

    def test_persistence(self):
        path = os.path.join(tempfile.mkdtemp(), "settings.json")
        s1 = Settings(path)
        s1.last_import_dir = "C:/test"
        s1.batch_size = 10
        s1.save()

        s2 = Settings(path)
        assert s2.last_import_dir == "C:/test"
        assert s2.batch_size == 10

    def test_auto_save_on_set(self):
        path = os.path.join(tempfile.mkdtemp(), "settings.json")
        s1 = Settings(path)
        s1.last_import_dir = "C:/auto"

        s2 = Settings(path)
        assert s2.last_import_dir == "C:/auto"

    def test_window_geometry(self):
        s = self._make_settings()
        s.window_width = 1200
        s.window_height = 800
        s.window_x = 100
        s.window_y = 50
        assert s.window_width == 1200
        assert s.window_x == 100
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_settings.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement Settings**

```python
# core/settings.py
import json
import os


_DEFAULTS = {
    "last_import_dir": "",
    "batch_size": 20,
    "window_width": 900,
    "window_height": 700,
    "window_x": -1,
    "window_y": -1,
    "last_template": "",
}


class Settings:
    """Persists user settings to a JSON file."""

    def __init__(self, path: str):
        self._path = path
        self._data = dict(_DEFAULTS)
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                stored = json.load(f)
            self._data.update(stored)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def _set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()

    @property
    def last_import_dir(self) -> str:
        return self._data["last_import_dir"]

    @last_import_dir.setter
    def last_import_dir(self, value: str) -> None:
        self._set("last_import_dir", value)

    @property
    def batch_size(self) -> int:
        return self._data["batch_size"]

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        self._set("batch_size", value)

    @property
    def window_width(self) -> int:
        return self._data["window_width"]

    @window_width.setter
    def window_width(self, value: int) -> None:
        self._set("window_width", value)

    @property
    def window_height(self) -> int:
        return self._data["window_height"]

    @window_height.setter
    def window_height(self, value: int) -> None:
        self._set("window_height", value)

    @property
    def window_x(self) -> int:
        return self._data["window_x"]

    @window_x.setter
    def window_x(self, value: int) -> None:
        self._set("window_x", value)

    @property
    def window_y(self) -> int:
        return self._data["window_y"]

    @window_y.setter
    def window_y(self, value: int) -> None:
        self._set("window_y", value)

    @property
    def last_template(self) -> str:
        return self._data["last_template"]

    @last_template.setter
    def last_template(self, value: str) -> None:
        self._set("last_template", value)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_settings.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/settings.py tests/test_settings.py
git commit -m "feat: add settings manager with JSON persistence"
```

---

### Task 10: PySide6 GUI — styles and main window shell

**Files:**
- Create: `gui/styles.py`
- Modify: `gui/app.py`
- Modify: `main.py`

- [ ] **Step 1: Create the QSS stylesheet module**

```python
# gui/styles.py

COLORS = {
    "bg": "#FAFBFC",
    "panel": "#FFFFFF",
    "accent": "#2563EB",
    "accent_dark": "#1D4ED8",
    "accent_light": "#DBEAFE",
    "success": "#16A34A",
    "error": "#DC2626",
    "error_light": "#FEE2E2",
    "text": "#1F2937",
    "text_secondary": "#6B7280",
    "text_dim": "#9CA3AF",
    "border": "#E5E7EB",
    "input_bg": "#F9FAFB",
    "input_focus": "#2563EB",
}

FONT_FAMILY = "Segoe UI"

QSS = f"""
QMainWindow {{
    background-color: {COLORS['bg']};
}}

QWidget {{
    font-family: "{FONT_FAMILY}";
    font-size: 13px;
    color: {COLORS['text']};
}}

QLabel {{
    color: {COLORS['text']};
    background: transparent;
}}

QLabel[class="dim"] {{
    color: {COLORS['text_secondary']};
    font-size: 12px;
}}

QLabel[class="header"] {{
    font-size: 18px;
    font-weight: bold;
    color: {COLORS['text']};
}}

QLabel[class="section"] {{
    font-size: 14px;
    font-weight: 600;
    color: {COLORS['text']};
}}

QPushButton {{
    background-color: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    color: {COLORS['text']};
}}

QPushButton:hover {{
    background-color: {COLORS['bg']};
    border-color: {COLORS['accent']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_light']};
}}

QPushButton:disabled {{
    color: {COLORS['text_dim']};
    border-color: {COLORS['border']};
    background-color: {COLORS['bg']};
}}

QPushButton[class="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_dark']});
    color: white;
    border: none;
    font-weight: bold;
    padding: 10px 24px;
}}

QPushButton[class="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['accent_dark']}, stop:1 #1E40AF);
}}

QPushButton[class="primary"]:disabled {{
    background: {COLORS['text_dim']};
}}

QPushButton[class="danger"] {{
    background-color: {COLORS['error']};
    color: white;
    border: none;
    font-weight: bold;
}}

QLineEdit, QComboBox {{
    background-color: {COLORS['input_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}}

QLineEdit:focus, QComboBox:focus {{
    border-color: {COLORS['input_focus']};
    background-color: white;
}}

QTextEdit {{
    background-color: {COLORS['input_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}}

QTextEdit:focus {{
    border-color: {COLORS['input_focus']};
    background-color: white;
}}

QTableWidget {{
    background-color: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 6px 8px;
}}

QHeaderView::section {{
    background-color: {COLORS['bg']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}

QProgressBar {{
    background-color: {COLORS['border']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_dark']});
    border-radius: 4px;
}}

QTabWidget::pane {{
    border: none;
    background: {COLORS['bg']};
}}

QTabBar::tab {{
    background: transparent;
    border: none;
    padding: 10px 20px;
    font-size: 13px;
    color: {COLORS['text_secondary']};
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:selected {{
    color: {COLORS['accent']};
    border-bottom-color: {COLORS['accent']};
    font-weight: bold;
}}

QTabBar::tab:hover {{
    color: {COLORS['text']};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['text_dim']};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QGroupBox {{
    background-color: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: 8px;
    padding: 16px;
    padding-top: 28px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: {COLORS['text_secondary']};
    font-size: 12px;
}}
"""
```

- [ ] **Step 2: Create the main window shell (gui/app.py)**

Replace the entire `gui/app.py` with the PySide6 main window:

```python
# gui/app.py
import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from gui.styles import QSS, COLORS


class SMSSenderApp:
    """Main application entry point."""

    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setStyleSheet(QSS)

        self._window = MainWindow()

    def run(self):
        self._window.show()
        sys.exit(self._app.exec())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMS Sender")
        self.setMinimumSize(900, 700)

        # Central widget with tabs
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        # Tabs — placeholders for now
        self._send_tab = QWidget()
        self._history_tab = QWidget()

        self._tabs.addTab(self._send_tab, "Wysylka")
        self._tabs.addTab(self._history_tab, "Historia")

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Gotowy")
```

- [ ] **Step 3: Update main.py**

```python
# main.py
from gui.app import SMSSenderApp


def main():
    app = SMSSenderApp()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the app to verify it launches**

Run: `python main.py`
Expected: PySide6 window opens with two tabs ("Wysylka" and "Historia"), clean light theme, professional styling. Close the window manually.

- [ ] **Step 5: Commit**

```bash
git add gui/styles.py gui/app.py main.py
git commit -m "feat: PySide6 main window shell with QSS styling"
```

---

### Task 11: Import panel widget

**Files:**
- Create: `gui/widgets/__init__.py`
- Create: `gui/widgets/import_panel.py`
- Modify: `gui/app.py`

- [ ] **Step 1: Create gui/widgets/__init__.py**

```python
# gui/widgets/__init__.py
```

- [ ] **Step 2: Create the import panel widget**

```python
# gui/widgets/import_panel.py
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFileDialog, QMessageBox, QGroupBox,
)
from PySide6.QtCore import Signal, Qt

from core.excel_importer import (
    import_from_excel, import_from_csv,
    detect_phone_column, detect_phone_column_csv,
    get_column_headers, deduplicate_numbers,
)
from core.clipboard_import import parse_clipboard_text
from gui.styles import COLORS


class DropZone(QLabel):
    """Label that accepts drag & drop of files."""

    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("Przeciagnij plik Excel/CSV tutaj lub Ctrl+V")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(48)
        self.setProperty("class", "dim")
        self._default_style = (
            f"border: 2px dashed {COLORS['border']}; "
            f"border-radius: 8px; "
            f"padding: 12px; "
            f"color: {COLORS['text_secondary']};"
        )
        self._hover_style = (
            f"border: 2px dashed {COLORS['accent']}; "
            f"border-radius: 8px; "
            f"padding: 12px; "
            f"color: {COLORS['accent']}; "
            f"background-color: {COLORS['accent_light']};"
        )
        self.setStyleSheet(self._default_style)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toLocalFile()
            if url.lower().endswith((".xlsx", ".csv")):
                event.acceptProposedAction()
                self.setStyleSheet(self._hover_style)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._default_style)

    def dropEvent(self, event):
        self.setStyleSheet(self._default_style)
        url = event.mimeData().urls()[0].toLocalFile()
        self.file_dropped.emit(url)


class ImportPanel(QGroupBox):
    """Panel for importing phone numbers from Excel/CSV, drag&drop, clipboard."""

    numbers_changed = Signal(list, list, list)  # numbers, skipped, row_data
    headers_changed = Signal(list)  # column headers

    def __init__(self, settings=None, parent=None):
        super().__init__("Import numerow", parent)
        self._settings = settings
        self._current_path = ""
        self._headers = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Row 1: Import button + column dropdown
        row1 = QHBoxLayout()

        self._btn_import = QPushButton("Importuj plik")
        self._btn_import.clicked.connect(self._on_import_click)
        row1.addWidget(self._btn_import)

        row1.addWidget(QLabel("Kolumna:"))

        self._combo_column = QComboBox()
        self._combo_column.setMinimumWidth(120)
        self._combo_column.setEnabled(False)
        self._combo_column.currentIndexChanged.connect(self._on_column_changed)
        row1.addWidget(self._combo_column)

        self._lbl_file = QLabel("Brak pliku")
        self._lbl_file.setProperty("class", "dim")
        row1.addWidget(self._lbl_file)
        row1.addStretch()

        layout.addLayout(row1)

        # Row 2: Drop zone
        self._drop_zone = DropZone()
        self._drop_zone.file_dropped.connect(self._load_file)
        layout.addWidget(self._drop_zone)

        # Row 3: Summary
        self._lbl_summary = QLabel("")
        self._lbl_summary.setProperty("class", "dim")
        layout.addWidget(self._lbl_summary)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Paste):
            self._on_paste()
        else:
            super().keyPressEvent(event)

    def _on_paste(self):
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text or not text.strip():
            return

        valid, skipped = parse_clipboard_text(text)
        if not valid:
            QMessageBox.warning(
                self, "Brak numerow",
                "Schowek nie zawiera prawidlowych numerow telefonow."
            )
            return

        self._lbl_file.setText("(ze schowka)")
        self._lbl_summary.setText(
            f"Wklejono: {len(valid)} numerow ({len(skipped)} pominietych)"
        )
        self.numbers_changed.emit(valid, skipped, [])

    def _on_import_click(self):
        initial_dir = ""
        if self._settings and self._settings.last_import_dir:
            initial_dir = self._settings.last_import_dir

        path, _ = QFileDialog.getOpenFileName(
            self, "Importuj plik",
            initial_dir,
            "Excel / CSV (*.xlsx *.csv);;Wszystkie pliki (*.*)",
        )
        if path:
            if self._settings:
                self._settings.last_import_dir = os.path.dirname(path)
            self._load_file(path)

    def _load_file(self, path: str):
        self._current_path = path
        filename = os.path.basename(path)
        is_csv = path.lower().endswith(".csv")

        try:
            if is_csv:
                detected = detect_phone_column_csv(path)
            else:
                detected = detect_phone_column(path)
                self._headers = get_column_headers(path)
        except Exception as e:
            QMessageBox.critical(self, "Blad", str(e))
            return

        # Populate column dropdown
        self._combo_column.blockSignals(True)
        self._combo_column.clear()

        max_cols = self._get_max_columns(path, is_csv)
        for i in range(max_cols):
            label = chr(65 + i) if i < 26 else f"Col{i + 1}"
            if self._headers and i < len(self._headers) and self._headers[i]:
                label = f"{chr(65 + i)} ({self._headers[i]})"
            if detected is not None and i == detected:
                label += " [auto]"
            self._combo_column.addItem(label, i)

        if detected is not None:
            self._combo_column.setCurrentIndex(detected)
        self._combo_column.setEnabled(True)
        self._combo_column.blockSignals(False)

        self._lbl_file.setText(filename)
        self._import_with_column(path, detected if detected is not None else 0)

    def _on_column_changed(self, index: int):
        if self._current_path and index >= 0:
            col = self._combo_column.currentData()
            self._import_with_column(self._current_path, col)

    def _import_with_column(self, path: str, column: int):
        is_csv = path.lower().endswith(".csv")
        try:
            if is_csv:
                valid, skipped, row_data = import_from_csv(path, column=column, return_rows=True)
            else:
                valid, skipped, row_data = import_from_excel(path, column=column, return_rows=True)
        except Exception as e:
            QMessageBox.critical(self, "Blad importu", str(e))
            return

        valid, dup_count = deduplicate_numbers(valid)
        dup_text = f", {dup_count} duplikatow usunietych" if dup_count > 0 else ""

        self._lbl_summary.setText(
            f"Zaladowano: {len(valid)} numerow ({len(skipped)} pominietych{dup_text})"
        )

        if self._headers:
            self.headers_changed.emit(self._headers)

        self.numbers_changed.emit(valid, skipped, row_data)

    def _get_max_columns(self, path: str, is_csv: bool) -> int:
        if is_csv:
            import csv as csv_mod
            with open(path, "r", encoding="utf-8") as f:
                reader = csv_mod.reader(f)
                for row in reader:
                    return len(row)
            return 1
        else:
            from openpyxl import load_workbook
            wb = load_workbook(path, read_only=True)
            ws = wb.active
            max_col = ws.max_column or 1
            wb.close()
            return max_col

    def set_enabled(self, enabled: bool):
        self._btn_import.setEnabled(enabled)
        self._combo_column.setEnabled(enabled and bool(self._current_path))
```

- [ ] **Step 3: Wire ImportPanel into MainWindow send tab**

Update `gui/app.py` — add the import panel to the send tab:

```python
# gui/app.py
import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar,
)
from PySide6.QtCore import Qt

from gui.styles import QSS
from gui.widgets.import_panel import ImportPanel


class SMSSenderApp:
    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setStyleSheet(QSS)
        self._window = MainWindow()

    def run(self):
        self._window.show()
        sys.exit(self._app.exec())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMS Sender")
        self.setMinimumSize(900, 700)

        self._numbers = []
        self._skipped = []
        self._row_data = []
        self._headers = []

        # Tabs
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._build_send_tab()
        self._build_history_tab()

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Gotowy")

    def _build_send_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Import panel
        self._import_panel = ImportPanel()
        self._import_panel.numbers_changed.connect(self._on_numbers_changed)
        self._import_panel.headers_changed.connect(self._on_headers_changed)
        layout.addWidget(self._import_panel)

        # Placeholder for remaining widgets (added in later tasks)
        layout.addStretch()

        self._tabs.addTab(tab, "Wysylka")

    def _build_history_tab(self):
        tab = QWidget()
        self._tabs.addTab(tab, "Historia")

    def _on_numbers_changed(self, numbers, skipped, row_data):
        self._numbers = numbers
        self._skipped = skipped
        self._row_data = row_data
        self._status.showMessage(f"{len(numbers)} numerow zaladowanych")

    def _on_headers_changed(self, headers):
        self._headers = headers
```

- [ ] **Step 4: Run the app and test import**

Run: `python main.py`
Expected: Window with import panel — click "Importuj plik", select an Excel, see column auto-detection, summary text. Close.

- [ ] **Step 5: Commit**

```bash
git add gui/widgets/__init__.py gui/widgets/import_panel.py gui/app.py
git commit -m "feat: add import panel with drag&drop, column detection, clipboard"
```

---

### Task 12: Message panel widget

**Files:**
- Create: `gui/widgets/message_panel.py`
- Modify: `gui/app.py`

- [ ] **Step 1: Create message panel**

```python
# gui/widgets/message_panel.py
import os

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QInputDialog, QMessageBox,
)
from PySide6.QtCore import Signal

from gui.styles import COLORS


class MessagePanel(QGroupBox):
    """Panel for composing SMS message with templates and character counter."""

    MAX_CHARS = 320
    message_changed = Signal(str)

    def __init__(self, template_manager=None, parent=None):
        super().__init__("Tresc SMS", parent)
        self._template_manager = template_manager
        self._headers = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Templates row
        row1 = QHBoxLayout()

        self._combo_templates = QComboBox()
        self._combo_templates.setMinimumWidth(200)
        self._combo_templates.addItem("-- Szablony --")
        self._combo_templates.currentIndexChanged.connect(self._on_template_selected)
        row1.addWidget(self._combo_templates)

        btn_save_tpl = QPushButton("Zapisz szablon")
        btn_save_tpl.clicked.connect(self._on_save_template)
        row1.addWidget(btn_save_tpl)

        btn_del_tpl = QPushButton("Usun szablon")
        btn_del_tpl.clicked.connect(self._on_delete_template)
        row1.addWidget(btn_del_tpl)

        row1.addStretch()
        layout.addLayout(row1)

        # Variables hint
        self._lbl_variables = QLabel("")
        self._lbl_variables.setProperty("class", "dim")
        self._lbl_variables.setWordWrap(True)
        layout.addWidget(self._lbl_variables)

        # Text editor
        self._editor = QTextEdit()
        self._editor.setMaximumHeight(100)
        self._editor.setPlaceholderText("Wpisz tresc wiadomosci...")
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

        # Char counter
        self._lbl_chars = QLabel("Znaki: 0/320 (1 SMS)")
        self._lbl_chars.setProperty("class", "dim")
        layout.addWidget(self._lbl_chars)

        # SMS count info
        self._lbl_sms_count = QLabel("")
        self._lbl_sms_count.setProperty("class", "dim")
        layout.addWidget(self._lbl_sms_count)

        self._refresh_templates()

    def set_headers(self, headers: list[str]):
        self._headers = headers
        if headers:
            vars_text = "Dostepne zmienne: " + ", ".join(
                f"{{{h}}}" for h in headers if h
            )
            self._lbl_variables.setText(vars_text)
        else:
            self._lbl_variables.setText("")

    def set_recipient_count(self, count: int):
        self._recipient_count = count
        self._update_sms_count()

    def get_message(self) -> str:
        return self._editor.toPlainText().strip()

    def _on_text_changed(self):
        text = self._editor.toPlainText()
        count = len(text)
        sms_parts = 1 if count <= 160 else 2
        color = COLORS["error"] if count > self.MAX_CHARS else COLORS["text_secondary"]

        self._lbl_chars.setText(f"Znaki: {count}/{self.MAX_CHARS} ({sms_parts} SMS)")
        self._lbl_chars.setStyleSheet(f"color: {color};")

        self._update_sms_count()
        self.message_changed.emit(text)

    def _update_sms_count(self):
        count = len(self._editor.toPlainText())
        recipients = getattr(self, "_recipient_count", 0)
        if recipients > 0 and count > 0:
            sms_parts = 1 if count <= 160 else 2
            total = recipients * sms_parts
            self._lbl_sms_count.setText(
                f"Odbiorcy: {recipients} x {sms_parts} SMS = {total} SMS-ow"
            )
        else:
            self._lbl_sms_count.setText("")

    def _on_template_selected(self, index: int):
        if index <= 0 or not self._template_manager:
            return
        name = self._combo_templates.currentText()
        content = self._template_manager.load(name)
        if content:
            self._editor.setPlainText(content)

    def _on_save_template(self):
        if not self._template_manager:
            return
        text = self._editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Pusta tresc", "Wpisz tresc szablonu")
            return

        name, ok = QInputDialog.getText(self, "Zapisz szablon", "Nazwa szablonu:")
        if ok and name.strip():
            self._template_manager.save(name.strip(), text)
            self._refresh_templates()

    def _on_delete_template(self):
        if not self._template_manager:
            return
        index = self._combo_templates.currentIndex()
        if index <= 0:
            return
        name = self._combo_templates.currentText()
        self._template_manager.delete(name)
        self._refresh_templates()

    def _refresh_templates(self):
        self._combo_templates.blockSignals(True)
        self._combo_templates.clear()
        self._combo_templates.addItem("-- Szablony --")
        if self._template_manager:
            for name in self._template_manager.list_names():
                self._combo_templates.addItem(name)
        self._combo_templates.blockSignals(False)
```

- [ ] **Step 2: Wire into MainWindow**

In `gui/app.py`, add to `_build_send_tab` after the import panel:

```python
from gui.widgets.message_panel import MessagePanel

# Inside _build_send_tab, after import_panel:
self._message_panel = MessagePanel()
self._message_panel.message_changed.connect(self._on_message_changed)
layout.addWidget(self._message_panel)
```

Add handler:

```python
def _on_message_changed(self, text):
    pass  # Will be used by preview table
```

Update `_on_numbers_changed`:

```python
def _on_numbers_changed(self, numbers, skipped, row_data):
    self._numbers = numbers
    self._skipped = skipped
    self._row_data = row_data
    self._message_panel.set_recipient_count(len(numbers))
    self._status.showMessage(f"{len(numbers)} numerow zaladowanych")
```

Update `_on_headers_changed`:

```python
def _on_headers_changed(self, headers):
    self._headers = headers
    self._message_panel.set_headers(headers)
```

- [ ] **Step 3: Run the app and test**

Run: `python main.py`
Expected: Message editor with template controls, character counter, SMS count. Close.

- [ ] **Step 4: Commit**

```bash
git add gui/widgets/message_panel.py gui/app.py
git commit -m "feat: add message panel with templates and character counter"
```

---

### Task 13: Preview table widget

**Files:**
- Create: `gui/widgets/preview_table.py`
- Modify: `gui/app.py`

- [ ] **Step 1: Create preview table**

```python
# gui/widgets/preview_table.py
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QWidget, QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal

from core.personalizer import Personalizer
from gui.styles import COLORS


class PreviewTable(QGroupBox):
    """Table showing recipients with personalized message preview."""

    selection_changed = Signal(list)  # list of selected indices

    def __init__(self, parent=None):
        super().__init__("Podglad odbiorcow", parent)
        self._numbers = []
        self._row_data = []
        self._headers = None
        self._template = ""
        self._checks = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["", "Numer", "Tresc"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 40)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._table.verticalHeader().setVisible(False)

        layout.addWidget(self._table)

    def update_data(self, numbers: list[str], row_data: list[list],
                    headers: list[str] | None, template: str):
        self._numbers = numbers
        self._row_data = row_data
        self._headers = headers
        self._template = template
        self._refresh()

    def update_template(self, template: str):
        self._template = template
        self._refresh()

    def get_selected_numbers(self) -> list[str]:
        selected = []
        for i, num in enumerate(self._numbers):
            if i < len(self._checks) and self._checks[i].isChecked():
                selected.append(num)
        return selected

    def get_selected_indices(self) -> list[int]:
        return [
            i for i in range(len(self._numbers))
            if i < len(self._checks) and self._checks[i].isChecked()
        ]

    def update_row_status(self, index: int, status: str):
        if index < self._table.rowCount():
            color = COLORS["success"] if status == "sent" else COLORS["error"]
            for col in range(self._table.columnCount()):
                item = self._table.item(index, col)
                if item:
                    item.setForeground(Qt.GlobalColor.white)
                    item.setBackground(Qt.GlobalColor.transparent)

            status_item = QTableWidgetItem(status)
            status_item.setForeground(
                Qt.GlobalColor.green if status == "sent"
                else Qt.GlobalColor.red
            )
            # Update the message column with status
            existing = self._table.item(index, 2)
            if existing:
                existing.setText(f"[{status.upper()}] {existing.text()}")

    def _refresh(self):
        self._table.setRowCount(len(self._numbers))
        self._checks = []

        personalizer = None
        if self._template and self._row_data:
            personalizer = Personalizer(self._template, self._headers)

        for i, num in enumerate(self._numbers):
            # Checkbox
            cb = QCheckBox()
            cb.setChecked(True)
            self._checks.append(cb)

            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(i, 0, cb_widget)

            # Number
            num_item = QTableWidgetItem(num)
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(i, 1, num_item)

            # Personalized message
            if personalizer and i < len(self._row_data):
                msg = personalizer.render(self._row_data[i])
            else:
                msg = self._template
            msg_item = QTableWidgetItem(msg)
            msg_item.setFlags(msg_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(i, 2, msg_item)
```

- [ ] **Step 2: Wire into MainWindow**

In `gui/app.py`, add after message panel:

```python
from gui.widgets.preview_table import PreviewTable

# Inside _build_send_tab, after message_panel:
self._preview_table = PreviewTable()
layout.addWidget(self._preview_table)
```

Update `_on_numbers_changed`:

```python
def _on_numbers_changed(self, numbers, skipped, row_data):
    self._numbers = numbers
    self._skipped = skipped
    self._row_data = row_data
    self._message_panel.set_recipient_count(len(numbers))
    self._preview_table.update_data(
        numbers, row_data, self._headers,
        self._message_panel.get_message(),
    )
    self._status.showMessage(f"{len(numbers)} numerow zaladowanych")
```

Update `_on_message_changed`:

```python
def _on_message_changed(self, text):
    self._preview_table.update_template(text)
```

- [ ] **Step 3: Run the app and test**

Run: `python main.py`
Expected: After import, preview table shows numbers with checkboxes and message preview. Typing in message field updates the preview in real-time. Close.

- [ ] **Step 4: Commit**

```bash
git add gui/widgets/preview_table.py gui/app.py
git commit -m "feat: add preview table with personalization and checkboxes"
```

---

### Task 14: Send panel widget (send/stop/resume, progress, log)

**Files:**
- Create: `gui/widgets/send_panel.py`
- Modify: `gui/app.py`

- [ ] **Step 1: Create send panel**

```python
# gui/widgets/send_panel.py
import time
import threading
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QTextEdit, QGroupBox, QMessageBox, QFileDialog,
)
from PySide6.QtCore import Signal, QMetaObject, Qt, Q_ARG, Slot

from core.batch_manager import BatchManager
from core.sender import PhoneLinkSender
from core.report import export_report_xlsx, export_report_csv
from gui.styles import COLORS


class SendPanel(QWidget):
    """Panel with send/stop/resume buttons, progress bar, and log."""

    status_update = Signal(int, str)  # recipient_index, status
    sending_finished = Signal(list)  # recipients results for history

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sender = PhoneLinkSender(on_log=self._log_threadsafe)
        self._sending = False
        self._stop_requested = False
        self._batch_manager = None
        self._results = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Buttons row
        btn_row = QHBoxLayout()

        self._btn_send = QPushButton("Wyslij")
        self._btn_send.setProperty("class", "primary")
        self._btn_send.setEnabled(False)
        self._btn_send.clicked.connect(self._on_send)
        btn_row.addWidget(self._btn_send)

        self._btn_stop = QPushButton("Stop")
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._on_stop)
        btn_row.addWidget(self._btn_stop)

        self._btn_resume = QPushButton("Wznow")
        self._btn_resume.setEnabled(False)
        self._btn_resume.clicked.connect(self._on_resume)
        btn_row.addWidget(self._btn_resume)

        btn_row.addStretch()

        self._btn_export = QPushButton("Eksportuj raport")
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._on_export)
        btn_row.addWidget(self._btn_export)

        layout.addLayout(btn_row)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setTextVisible(False)
        self._progress.setMaximumHeight(8)
        layout.addWidget(self._progress)

        self._lbl_progress = QLabel("")
        self._lbl_progress.setProperty("class", "dim")
        layout.addWidget(self._lbl_progress)

        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        self._txt_log = QTextEdit()
        self._txt_log.setReadOnly(True)
        self._txt_log.setMaximumHeight(150)
        self._txt_log.setStyleSheet(
            f"background-color: {COLORS['bg']}; "
            f"color: {COLORS['text_secondary']}; "
            f"font-size: 11px; font-family: 'Consolas';"
        )
        log_layout.addWidget(self._txt_log)
        layout.addWidget(log_group)

    def set_ready(self, has_numbers: bool, has_message: bool):
        can_send = has_numbers and has_message and not self._sending
        self._btn_send.setEnabled(can_send)

    def set_data(self, numbers, message, get_selected_fn):
        self._numbers = numbers
        self._message = message
        self._get_selected = get_selected_fn

    @Slot()
    def _on_send(self):
        selected = self._get_selected()
        if not selected:
            QMessageBox.warning(self, "Brak odbiorcow", "Zaznacz odbiorcow do wysylki")
            return
        if not self._message:
            QMessageBox.warning(self, "Brak tresci", "Wpisz tresc wiadomosci")
            return

        QMessageBox.warning(
            self, "Uwaga",
            "Nie ruszaj myszka ani klawiatura podczas wysylki.\n"
            "Komputer bedzie zablokowany na czas automatyzacji.",
        )

        self._batch_manager = BatchManager(selected, batch_size=20)
        self._results = []
        self._start_sending()

    @Slot()
    def _on_stop(self):
        self._stop_requested = True
        self._log("Zatrzymywanie wysylki...")

    @Slot()
    def _on_resume(self):
        self._start_sending()

    def _start_sending(self):
        self._sending = True
        self._stop_requested = False
        self._btn_send.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._btn_resume.setEnabled(False)
        self._btn_export.setEnabled(False)

        thread = threading.Thread(target=self._send_loop, daemon=True)
        thread.start()

    def _send_loop(self):
        bm = self._batch_manager
        total = bm.total_batches

        self._progress.setMaximum(total)
        self._progress.setValue(0)

        try:
            self._sender._automation.connect()
        except Exception as e:
            self._log(f"BLAD: {e}")
            self._finish_sending()
            return

        while True:
            idx = bm.next_pending_index()
            if idx is None or self._stop_requested:
                break

            batch = bm.get_batch(idx)
            self._log(f"Paczka {idx + 1}/{total} ({len(batch)} numerow)...")
            self._lbl_progress.setText(f"Paczka {idx + 1}/{total}")

            try:
                self._sender.send(batch, self._message)
                bm.mark_sent(idx)
                self._log(f"Paczka {idx + 1}/{total} wyslana")

                for num in batch:
                    self._results.append({
                        "number": num,
                        "status": "sent",
                        "message": self._message,
                        "time": time.strftime("%H:%M:%S"),
                        "error": "",
                    })
            except Exception as e:
                bm.mark_error(idx, str(e))
                self._log(f"BLAD paczka {idx + 1}/{total}: {e}")

                for num in batch:
                    self._results.append({
                        "number": num,
                        "status": "error",
                        "message": self._message,
                        "time": time.strftime("%H:%M:%S"),
                        "error": str(e),
                    })

                self._finish_sending()
                return

            self._progress.setValue(idx + 1)

            if bm.next_pending_index() is not None:
                delay = random.uniform(4.0, 8.0)
                self._log(f"Czekam {delay:.1f}s przed nastepna paczka...")
                time.sleep(delay)

        summary = bm.summary()
        self._log(
            f"Zakonczono: {summary['sent']} wyslanych, "
            f"{summary['error']} bledow, {summary['pending']} oczekujacych"
        )
        self._finish_sending()

    def _finish_sending(self):
        self._sending = False
        self._btn_send.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._btn_export.setEnabled(bool(self._results))

        if self._batch_manager:
            summary = self._batch_manager.summary()
            if summary["error"] > 0 or summary["pending"] > 0:
                self._btn_resume.setEnabled(True)

        self.sending_finished.emit(self._results)

    @Slot()
    def _on_export(self):
        if not self._results:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Eksportuj raport",
            f"raport_SMS_{time.strftime('%Y-%m-%d_%H%M%S')}.xlsx",
            "Excel (*.xlsx);;CSV (*.csv)",
        )
        if not path:
            return

        if path.lower().endswith(".csv"):
            export_report_csv(path, self._results)
        else:
            export_report_xlsx(path, self._results)

        self._log(f"Raport wyeksportowany: {path}")

    def _log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"{timestamp} {message}"
        self._txt_log.append(line)
        scrollbar = self._txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _log_threadsafe(self, message: str):
        self._log(message)
```

- [ ] **Step 2: Wire into MainWindow**

In `gui/app.py`, add after preview table:

```python
from gui.widgets.send_panel import SendPanel

# Inside _build_send_tab, after preview_table:
self._send_panel = SendPanel()
self._send_panel.sending_finished.connect(self._on_sending_finished)
layout.addWidget(self._send_panel)
```

Add/update handlers:

```python
def _on_message_changed(self, text):
    self._preview_table.update_template(text)
    self._send_panel.set_ready(
        has_numbers=bool(self._numbers),
        has_message=bool(text.strip()),
    )
    self._send_panel.set_data(
        self._numbers, text.strip(),
        self._preview_table.get_selected_numbers,
    )

def _on_numbers_changed(self, numbers, skipped, row_data):
    self._numbers = numbers
    self._skipped = skipped
    self._row_data = row_data
    self._message_panel.set_recipient_count(len(numbers))
    self._preview_table.update_data(
        numbers, row_data, self._headers,
        self._message_panel.get_message(),
    )
    self._send_panel.set_ready(
        has_numbers=bool(numbers),
        has_message=bool(self._message_panel.get_message()),
    )
    self._send_panel.set_data(
        numbers, self._message_panel.get_message(),
        self._preview_table.get_selected_numbers,
    )
    self._status.showMessage(f"{len(numbers)} numerow zaladowanych")

def _on_sending_finished(self, results):
    self._status.showMessage("Wysylka zakonczona")
```

Remove the `layout.addStretch()` from `_build_send_tab` (no longer needed).

- [ ] **Step 3: Run the app and test the full send flow visually**

Run: `python main.py`
Expected: Full send tab with import → message → preview → send/stop/resume/export. Close.

- [ ] **Step 4: Commit**

```bash
git add gui/widgets/send_panel.py gui/app.py
git commit -m "feat: add send panel with progress, log, and report export"
```

---

### Task 15: History view widget

**Files:**
- Create: `gui/widgets/history_view.py`
- Modify: `gui/app.py`

- [ ] **Step 1: Create history view**

```python
# gui/widgets/history_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QTextEdit, QGroupBox, QSplitter,
)
from PySide6.QtCore import Qt

from core.history import HistoryManager


class HistoryView(QWidget):
    """View for browsing SMS sending history."""

    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self._hm = history_manager
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Sessions table
        sessions_group = QGroupBox("Sesje wysylki")
        sessions_layout = QVBoxLayout(sessions_group)

        self._sessions_table = QTableWidget()
        self._sessions_table.setColumnCount(5)
        self._sessions_table.setHorizontalHeaderLabels([
            "Data", "Plik", "Tresc", "Wyslano", "Bledy"
        ])
        self._sessions_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._sessions_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._sessions_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self._sessions_table.verticalHeader().setVisible(False)
        self._sessions_table.currentCellChanged.connect(self._on_session_selected)
        sessions_layout.addWidget(self._sessions_table)

        splitter.addWidget(sessions_group)

        # Session details
        details_group = QGroupBox("Szczegoly sesji")
        details_layout = QVBoxLayout(details_group)

        self._details_table = QTableWidget()
        self._details_table.setColumnCount(3)
        self._details_table.setHorizontalHeaderLabels(["Numer", "Status", "Blad"])
        self._details_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._details_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._details_table.verticalHeader().setVisible(False)
        details_layout.addWidget(self._details_table)

        splitter.addWidget(details_group)

        layout.addWidget(splitter)

    def refresh(self):
        sessions = self._hm.list_sessions()
        self._sessions_table.setRowCount(len(sessions))
        self._session_ids = []

        for i, s in enumerate(sessions):
            self._session_ids.append(s["id"])

            date_item = QTableWidgetItem(s["created_at"][:19].replace("T", " "))
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 0, date_item)

            file_item = QTableWidgetItem(s["source_file"])
            file_item.setFlags(file_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 1, file_item)

            msg_item = QTableWidgetItem(s["message"][:60])
            msg_item.setFlags(msg_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 2, msg_item)

            sent_item = QTableWidgetItem(str(s["sent"]))
            sent_item.setFlags(sent_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 3, sent_item)

            err_item = QTableWidgetItem(str(s["errors"]))
            err_item.setFlags(err_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._sessions_table.setItem(i, 4, err_item)

    def _on_session_selected(self, row, col, prev_row, prev_col):
        if row < 0 or row >= len(self._session_ids):
            return

        session = self._hm.get_session(self._session_ids[row])
        if not session:
            return

        recipients = session["recipients"]
        self._details_table.setRowCount(len(recipients))

        for i, r in enumerate(recipients):
            num_item = QTableWidgetItem(r["number"])
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._details_table.setItem(i, 0, num_item)

            status_item = QTableWidgetItem(r["status"])
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._details_table.setItem(i, 1, status_item)

            error_item = QTableWidgetItem(r.get("error", "") or "")
            error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._details_table.setItem(i, 2, error_item)
```

- [ ] **Step 2: Wire into MainWindow**

Replace `_build_history_tab` in `gui/app.py`:

```python
import os
from gui.widgets.history_view import HistoryView
from core.history import HistoryManager

# Add to __init__, before tabs:
appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
self._data_dir = os.path.join(appdata, "SMSSender")
self._history_manager = HistoryManager(os.path.join(self._data_dir, "history.db"))

# Replace _build_history_tab:
def _build_history_tab(self):
    self._history_view = HistoryView(self._history_manager)
    self._tabs.addTab(self._history_view, "Historia")
    self._tabs.currentChanged.connect(self._on_tab_changed)

def _on_tab_changed(self, index):
    if index == 1:
        self._history_view.refresh()
```

Update `_on_sending_finished` to save to history:

```python
def _on_sending_finished(self, results):
    source = self._import_panel._lbl_file.text() if hasattr(self, '_import_panel') else ""
    self._history_manager.save_session(
        message=self._message_panel.get_message(),
        source_file=source,
        recipients=results,
    )
    self._status.showMessage("Wysylka zakonczona")
```

- [ ] **Step 3: Run the app and test history tab**

Run: `python main.py`
Expected: History tab shows sessions list and clicking a session shows details.

- [ ] **Step 4: Commit**

```bash
git add gui/widgets/history_view.py gui/app.py
git commit -m "feat: add history view with session details"
```

---

### Task 16: Wire settings and template manager into app

**Files:**
- Modify: `gui/app.py`

- [ ] **Step 1: Initialize settings and template manager in MainWindow**

Add to `gui/app.py` imports and `__init__`:

```python
from core.settings import Settings
from core.template_manager import TemplateManager

# In __init__, after data_dir:
self._settings = Settings(os.path.join(self._data_dir, "settings.json"))
self._template_manager = TemplateManager(os.path.join(self._data_dir, "templates.json"))
```

- [ ] **Step 2: Pass settings to ImportPanel and TemplateManager to MessagePanel**

Update `_build_send_tab`:

```python
self._import_panel = ImportPanel(settings=self._settings)
self._message_panel = MessagePanel(template_manager=self._template_manager)
```

- [ ] **Step 3: Restore and save window geometry**

Add to `__init__` after building tabs:

```python
# Restore geometry
if self._settings.window_x >= 0:
    self.setGeometry(
        self._settings.window_x, self._settings.window_y,
        self._settings.window_width, self._settings.window_height,
    )
else:
    self.resize(self._settings.window_width, self._settings.window_height)
```

Override `closeEvent`:

```python
def closeEvent(self, event):
    geo = self.geometry()
    self._settings.window_width = geo.width()
    self._settings.window_height = geo.height()
    self._settings.window_x = geo.x()
    self._settings.window_y = geo.y()
    super().closeEvent(event)
```

- [ ] **Step 4: Run the app, resize window, close, reopen — verify geometry restores**

Run: `python main.py` — resize window, close. Run again — should restore size/position.

- [ ] **Step 5: Commit**

```bash
git add gui/app.py
git commit -m "feat: wire settings and template manager into main app"
```

---

### Task 17: Final GUI assembly and Ctrl+V support

**Files:**
- Modify: `gui/app.py`

- [ ] **Step 1: Add Ctrl+V handler to MainWindow**

Add method to `MainWindow`:

```python
from PySide6.QtGui import QKeySequence, QShortcut

# In __init__, after building tabs:
paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
paste_shortcut.activated.connect(self._on_global_paste)

def _on_global_paste(self):
    from PySide6.QtWidgets import QApplication
    from core.clipboard_import import parse_clipboard_text

    # Only paste numbers if on the send tab and message editor doesn't have focus
    if self._tabs.currentIndex() != 0:
        return
    if self._message_panel._editor.hasFocus():
        return

    clipboard = QApplication.clipboard()
    text = clipboard.text()
    if not text or not text.strip():
        return

    valid, skipped = parse_clipboard_text(text)
    if not valid:
        return

    from core.excel_importer import deduplicate_numbers
    combined = self._numbers + valid
    combined, dup_count = deduplicate_numbers(combined)

    self._on_numbers_changed(combined, skipped, self._row_data)
    self._status.showMessage(
        f"Wklejono {len(valid)} numerow ({dup_count} duplikatow usunietych)"
    )
```

- [ ] **Step 2: Run and test Ctrl+V**

Run: `python main.py`
Open Excel, copy a column of phone numbers, switch to SMS Sender, press Ctrl+V.
Expected: Numbers appear in preview table.

- [ ] **Step 3: Commit**

```bash
git add gui/app.py
git commit -m "feat: add global Ctrl+V paste for phone numbers"
```

---

### Task 18: PyInstaller build script

**Files:**
- Create: `installer/build.py`
- Create: `installer/sms_sender.spec` (auto-generated)

- [ ] **Step 1: Create build script**

```python
# installer/build.py
"""Build SMS Sender into a distributable package using PyInstaller."""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "SMSSender",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", f"{os.path.join(ROOT, 'gui')}:gui",
        os.path.join(ROOT, "main.py"),
    ]

    icon_path = os.path.join(ROOT, "installer", "icon.ico")
    if os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)
    print("\nBuild complete! Output in dist/SMSSender/")


if __name__ == "__main__":
    build()
```

- [ ] **Step 2: Test the build**

Run: `python installer/build.py`
Expected: Build completes, `dist/SMSSender/SMSSender.exe` exists.

- [ ] **Step 3: Test the built exe**

Run: `dist/SMSSender/SMSSender.exe`
Expected: App launches with full UI.

- [ ] **Step 4: Commit**

```bash
git add installer/build.py
git commit -m "feat: add PyInstaller build script"
```

---

### Task 19: Inno Setup installer script

**Files:**
- Create: `installer/sms_sender.iss`

- [ ] **Step 1: Create Inno Setup script**

```iss
; installer/sms_sender.iss
; Inno Setup script for SMS Sender

#define MyAppName "SMS Sender"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "SMS Sender"
#define MyAppExeName "SMSSender.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist\installer
OutputBaseFilename=SMSSender_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\SMSSender\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
```

- [ ] **Step 2: Add build instructions to a comment in the script**

The script is ready. To build the installer:
1. Install Inno Setup from https://jrsoftware.org/isinfo.php
2. Run: `python installer/build.py` (creates dist/SMSSender/)
3. Open `installer/sms_sender.iss` in Inno Setup Compiler and click Build
4. Or via command line: `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\sms_sender.iss`

Output: `dist/installer/SMSSender_Setup_2.0.0.exe`

- [ ] **Step 3: Commit**

```bash
git add installer/sms_sender.iss
git commit -m "feat: add Inno Setup installer script"
```

---

### Task 20: Update .gitignore, requirements, and cleanup

**Files:**
- Modify: `.gitignore`
- Modify: `requirements.txt`
- Delete: `gui/__pycache__/` (if exists)

- [ ] **Step 1: Update .gitignore with build artifacts**

Add to `.gitignore`:

```
# Build
build/
dist/
*.spec
```

- [ ] **Step 2: Verify all tests pass**

Run: `pytest tests/ -v`
Expected: All tests PASS (old + new)

- [ ] **Step 3: Run the app end-to-end**

Run: `python main.py`
Verify: Import → message with variables → preview → templates → send flow → history tab. Close.

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: update gitignore with build artifacts, final cleanup"
```
