# SMS Sender Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a desktop app that imports phone numbers from Excel and sends SMS messages through Windows Phone Link using pywinauto UI automation.

**Architecture:** Layered design with ExcelImporter → BatchManager → SMSSender interface → PhoneLinkSender. GUI in tkinter. All modules loosely coupled — sender is swappable (future ADB support).

**Tech Stack:** Python 3.12+, tkinter, openpyxl, pywinauto (UIA backend), phonenumbers

**Spec:** `docs/superpowers/specs/2026-04-09-sms-sender-design.md`

---

## File Structure

```
sms-sender/
├── main.py                      # Entry point
├── gui/
│   ├── __init__.py
│   └── app.py                   # Tkinter GUI — single window
├── core/
│   ├── __init__.py
│   ├── excel_importer.py        # Excel/CSV loading + phone number validation
│   ├── batch_manager.py         # Split numbers into batches ≤20, track status
│   └── sender.py                # SMSSender ABC + PhoneLinkSender
├── automation/
│   ├── __init__.py
│   └── phone_link.py            # pywinauto UIA automation sequence
├── tests/
│   ├── __init__.py
│   ├── test_excel_importer.py
│   ├── test_batch_manager.py
│   └── test_sender.py
├── requirements.txt
└── README.md
```

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `main.py`
- Create: `gui/__init__.py`, `core/__init__.py`, `automation/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
openpyxl>=3.1.0
pywinauto>=0.6.8
phonenumbers>=8.13.0
```

- [ ] **Step 2: Create empty __init__.py files and main.py stub**

`gui/__init__.py`, `core/__init__.py`, `automation/__init__.py`, `tests/__init__.py` — all empty files.

`main.py`:
```python
from gui.app import SMSSenderApp


def main():
    app = SMSSenderApp()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Install dependencies**

Run: `cd C:\Users\sadza\PycharmProjects\sms-sender && pip install -r requirements.txt`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: project setup with dependencies and structure"
```

---

### Task 2: ExcelImporter — Phone Number Validation

**Files:**
- Create: `core/excel_importer.py`
- Create: `tests/test_excel_importer.py`

- [ ] **Step 1: Write failing tests for phone number validation**

`tests/test_excel_importer.py`:
```python
import pytest
from core.excel_importer import normalize_phone_number, validate_phone_number


class TestNormalizePhoneNumber:
    def test_full_international_format(self):
        assert normalize_phone_number("+48512345678") == "+48512345678"

    def test_without_plus(self):
        assert normalize_phone_number("48512345678") == "+48512345678"

    def test_local_nine_digits(self):
        assert normalize_phone_number("512345678") == "+48512345678"

    def test_with_spaces(self):
        assert normalize_phone_number("+48 512 345 678") == "+48512345678"

    def test_with_dashes(self):
        assert normalize_phone_number("+48-512-345-678") == "+48512345678"

    def test_numeric_input(self):
        assert normalize_phone_number(512345678) == "+48512345678"


class TestValidatePhoneNumber:
    def test_valid_number(self):
        valid, number, reason = validate_phone_number("+48512345678")
        assert valid is True
        assert number == "+48512345678"
        assert reason is None

    def test_too_short(self):
        valid, number, reason = validate_phone_number("12345")
        assert valid is False
        assert reason is not None

    def test_letters_in_number(self):
        valid, number, reason = validate_phone_number("abc def ghi")
        assert valid is False
        assert reason is not None

    def test_empty_string(self):
        valid, number, reason = validate_phone_number("")
        assert valid is False
        assert reason is not None

    def test_none_value(self):
        valid, number, reason = validate_phone_number(None)
        assert valid is False
        assert reason is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_excel_importer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.excel_importer'`

- [ ] **Step 3: Implement phone number validation**

`core/excel_importer.py`:
```python
import phonenumbers


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_excel_importer.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add core/excel_importer.py tests/test_excel_importer.py
git commit -m "feat: phone number validation and normalization"
```

---

### Task 3: ExcelImporter — File Loading

**Files:**
- Modify: `core/excel_importer.py`
- Modify: `tests/test_excel_importer.py`

- [ ] **Step 1: Write failing tests for Excel/CSV loading**

Add to `tests/test_excel_importer.py`:
```python
import os
import tempfile
from openpyxl import Workbook
from core.excel_importer import import_from_excel, import_from_csv


class TestImportFromExcel:
    def _create_xlsx(self, numbers: list) -> str:
        """Helper: create a temp .xlsx with numbers in column A."""
        wb = Workbook()
        ws = wb.active
        for i, num in enumerate(numbers, start=1):
            ws.cell(row=i, column=1, value=num)
        path = os.path.join(tempfile.mkdtemp(), "test.xlsx")
        wb.save(path)
        return path

    def test_valid_numbers(self):
        path = self._create_xlsx(["+48512345678", "601234567", "48701234567"])
        valid, skipped = import_from_excel(path)
        assert len(valid) == 3
        assert all(n.startswith("+48") for n in valid)
        assert len(skipped) == 0

    def test_mixed_valid_and_invalid(self):
        path = self._create_xlsx(["+48512345678", "abc", "", "601234567"])
        valid, skipped = import_from_excel(path)
        assert len(valid) == 2
        assert len(skipped) == 2

    def test_empty_file(self):
        path = self._create_xlsx([])
        valid, skipped = import_from_excel(path)
        assert len(valid) == 0
        assert len(skipped) == 0

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            import_from_excel("/nonexistent/file.xlsx")


class TestImportFromCSV:
    def _create_csv(self, numbers: list) -> str:
        path = os.path.join(tempfile.mkdtemp(), "test.csv")
        with open(path, "w") as f:
            for num in numbers:
                f.write(f"{num}\n")
        return path

    def test_valid_numbers(self):
        path = self._create_csv(["+48512345678", "601234567"])
        valid, skipped = import_from_csv(path)
        assert len(valid) == 2

    def test_mixed(self):
        path = self._create_csv(["+48512345678", "bad", "601234567"])
        valid, skipped = import_from_csv(path)
        assert len(valid) == 2
        assert len(skipped) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_excel_importer.py -v -k "Import"`
Expected: FAIL — `ImportError: cannot import name 'import_from_excel'`

- [ ] **Step 3: Implement file loading**

Add to `core/excel_importer.py`:
```python
import csv
import os

from openpyxl import load_workbook


def import_from_excel(path: str) -> tuple[list[str], list[dict]]:
    """Import phone numbers from .xlsx file (column A).

    Returns: (valid_numbers, skipped_entries)
    skipped_entries: [{"row": int, "value": str, "reason": str}, ...]
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_excel_importer.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add core/excel_importer.py tests/test_excel_importer.py
git commit -m "feat: Excel and CSV file import with validation"
```

---

### Task 4: BatchManager

**Files:**
- Create: `core/batch_manager.py`
- Create: `tests/test_batch_manager.py`

- [ ] **Step 1: Write failing tests**

`tests/test_batch_manager.py`:
```python
from core.batch_manager import BatchManager


class TestBatchManager:
    def test_single_batch(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(10)], batch_size=20)
        assert bm.total_batches == 1
        assert len(bm.get_batch(0)) == 10

    def test_exact_split(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(40)], batch_size=20)
        assert bm.total_batches == 2
        assert len(bm.get_batch(0)) == 20
        assert len(bm.get_batch(1)) == 20

    def test_uneven_split(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(25)], batch_size=20)
        assert bm.total_batches == 2
        assert len(bm.get_batch(0)) == 20
        assert len(bm.get_batch(1)) == 5

    def test_empty_list(self):
        bm = BatchManager([], batch_size=20)
        assert bm.total_batches == 0

    def test_status_tracking(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(25)], batch_size=20)
        assert bm.get_status(0) == "pending"
        bm.mark_sent(0)
        assert bm.get_status(0) == "sent"
        bm.mark_error(1, "Phone Link nie odpowiada")
        assert bm.get_status(1) == "error"

    def test_resume_from_first_pending(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(60)], batch_size=20)
        bm.mark_sent(0)
        bm.mark_sent(1)
        assert bm.next_pending_index() == 2

    def test_resume_all_sent(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(20)], batch_size=20)
        bm.mark_sent(0)
        assert bm.next_pending_index() is None

    def test_resume_skips_error(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(60)], batch_size=20)
        bm.mark_sent(0)
        bm.mark_error(1, "error")
        assert bm.next_pending_index() == 1

    def test_summary(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(60)], batch_size=20)
        bm.mark_sent(0)
        bm.mark_sent(1)
        bm.mark_error(2, "timeout")
        summary = bm.summary()
        assert summary["sent"] == 2
        assert summary["error"] == 1
        assert summary["pending"] == 0
        assert summary["total"] == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_batch_manager.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement BatchManager**

`core/batch_manager.py`:
```python
import math


class BatchManager:
    def __init__(self, numbers: list[str], batch_size: int = 20):
        self._numbers = list(numbers)
        self._batch_size = batch_size
        self._batches: list[list[str]] = []
        self._statuses: list[str] = []  # "pending", "sent", "error"
        self._errors: list[str | None] = []

        for i in range(0, len(self._numbers), self._batch_size):
            self._batches.append(self._numbers[i : i + self._batch_size])
            self._statuses.append("pending")
            self._errors.append(None)

    @property
    def total_batches(self) -> int:
        return len(self._batches)

    def get_batch(self, index: int) -> list[str]:
        return self._batches[index]

    def get_status(self, index: int) -> str:
        return self._statuses[index]

    def mark_sent(self, index: int) -> None:
        self._statuses[index] = "sent"

    def mark_error(self, index: int, reason: str) -> None:
        self._statuses[index] = "error"
        self._errors[index] = reason

    def next_pending_index(self) -> int | None:
        """Return index of next batch to send (pending or error). None if all sent."""
        for i, status in enumerate(self._statuses):
            if status != "sent":
                return i
        return None

    def summary(self) -> dict:
        return {
            "total": self.total_batches,
            "sent": self._statuses.count("sent"),
            "error": self._statuses.count("error"),
            "pending": self._statuses.count("pending"),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_batch_manager.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add core/batch_manager.py tests/test_batch_manager.py
git commit -m "feat: BatchManager with status tracking and resume"
```

---

### Task 5: SMSSender Interface

**Files:**
- Create: `core/sender.py`
- Create: `tests/test_sender.py`

- [ ] **Step 1: Write failing tests for the interface contract**

`tests/test_sender.py`:
```python
from core.sender import SMSSender


class FakeSender(SMSSender):
    def __init__(self):
        self.sent = []

    def send(self, numbers: list[str], message: str) -> None:
        self.sent.append({"numbers": numbers, "message": message})

    def is_available(self) -> bool:
        return True


class TestSMSSenderInterface:
    def test_fake_sender_implements_interface(self):
        sender = FakeSender()
        sender.send(["+48512345678"], "Test")
        assert len(sender.sent) == 1
        assert sender.sent[0]["numbers"] == ["+48512345678"]
        assert sender.sent[0]["message"] == "Test"

    def test_is_available(self):
        sender = FakeSender()
        assert sender.is_available() is True

    def test_cannot_instantiate_abstract(self):
        import pytest
        with pytest.raises(TypeError):
            SMSSender()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_sender.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement SMSSender ABC**

`core/sender.py`:
```python
from abc import ABC, abstractmethod


class SMSSender(ABC):
    @abstractmethod
    def send(self, numbers: list[str], message: str) -> None:
        """Send an SMS to the given numbers with the given message."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the sender backend is available and ready."""
        ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_sender.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add core/sender.py tests/test_sender.py
git commit -m "feat: SMSSender abstract interface"
```

---

### Task 6: PhoneLinkSender — Automation Core

**Files:**
- Create: `automation/phone_link.py`

This task cannot be fully TDD-tested (requires a running Phone Link instance). We write the code with careful structure and test it manually.

- [ ] **Step 1: Implement clipboard helper**

`automation/phone_link.py`:
```python
import random
import time
import ctypes
import ctypes.wintypes

from pywinauto import Application, Desktop


def _save_clipboard() -> str | None:
    """Save current clipboard text content."""
    try:
        ctypes.windll.user32.OpenClipboard(0)
        handle = ctypes.windll.user32.GetClipboardData(13)  # CF_UNICODETEXT
        if handle:
            data = ctypes.c_wchar_p(handle).value
            ctypes.windll.user32.CloseClipboard()
            return data
        ctypes.windll.user32.CloseClipboard()
        return None
    except Exception:
        try:
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass
        return None


def _restore_clipboard(text: str | None) -> None:
    """Restore clipboard text content."""
    if text is None:
        return
    try:
        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        h_mem = ctypes.windll.kernel32.GlobalAlloc(0x0042, (len(text) + 1) * 2)
        p_mem = ctypes.windll.kernel32.GlobalLock(h_mem)
        ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(p_mem), text)
        ctypes.windll.kernel32.GlobalUnlock(h_mem)
        ctypes.windll.user32.SetClipboardData(13, h_mem)
        ctypes.windll.user32.CloseClipboard()
    except Exception:
        try:
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass
```

- [ ] **Step 2: Implement PhoneLinkSender class**

Add to `automation/phone_link.py`:
```python
class PhoneLinkAutomationError(Exception):
    """Raised when Phone Link automation fails."""
    pass


class PhoneLinkSender:
    WAIT_TIMEOUT = 10  # seconds

    def __init__(self, on_log=None):
        """
        Args:
            on_log: Optional callback(message: str) for logging actions.
        """
        self._app = None
        self._main_window = None
        self._on_log = on_log or (lambda msg: None)

    def _log(self, message: str) -> None:
        self._on_log(message)

    def connect(self) -> None:
        """Connect to the Phone Link application window."""
        self._log("Szukam okna Phone Link...")
        try:
            desktop = Desktop(backend="uia")
            self._main_window = desktop.window(title_re=".*Phone Link.*")
            self._main_window.wait("visible", timeout=self.WAIT_TIMEOUT)
            self._main_window.set_focus()
            self._log("Polaczono z Phone Link")
        except Exception as e:
            raise PhoneLinkAutomationError(
                "Nie znaleziono okna Phone Link. Upewnij sie, ze Phone Link jest otwarty i telefon polaczony."
            ) from e

    def is_available(self) -> bool:
        """Check if Phone Link window is visible."""
        try:
            desktop = Desktop(backend="uia")
            win = desktop.window(title_re=".*Phone Link.*")
            win.wait("visible", timeout=3)
            return True
        except Exception:
            return False

    def send_batch(self, numbers: list[str], message: str) -> None:
        """Send an SMS to a batch of numbers (max 20)."""
        if not self._main_window:
            self.connect()

        self._log(f"Wysylam paczke: {len(numbers)} numerow")

        # Step 1: Click Messages tab
        self._click_element("Messages", "TabItem")

        # Step 2: Click New Message
        self._click_element("New message", "Button")

        # Step 3: Add recipients
        for i, number in enumerate(numbers):
            self._log(f"  Dodaje odbierce {i+1}/{len(numbers)}: {number}")
            to_field = self._find_element("To", "Edit")
            to_field.click_input()
            to_field.type_keys(number, with_spaces=True)
            time.sleep(0.3)
            to_field.type_keys("{ENTER}")
            time.sleep(0.5)

        # Step 4: Type message with clipboard protection
        self._log("Wklejam tresc wiadomosci...")
        saved_clipboard = _save_clipboard()
        try:
            msg_field = self._find_element_by_type("Edit", occurrence=2)
            msg_field.click_input()

            # Copy message to clipboard and paste
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            h_mem = ctypes.windll.kernel32.GlobalAlloc(0x0042, (len(message) + 1) * 2)
            p_mem = ctypes.windll.kernel32.GlobalLock(h_mem)
            ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(p_mem), message)
            ctypes.windll.kernel32.GlobalUnlock(h_mem)
            ctypes.windll.user32.SetClipboardData(13, h_mem)
            ctypes.windll.user32.CloseClipboard()

            msg_field.type_keys("^v")  # Ctrl+V
        finally:
            _restore_clipboard(saved_clipboard)

        # Step 5: Click Send
        time.sleep(0.3)
        self._click_element("Send", "Button")
        self._log("Paczka wyslana!")

    def _find_element(self, title: str, control_type: str):
        """Find a UI element by title and control type."""
        try:
            elem = self._main_window.child_window(
                title=title, control_type=control_type
            )
            elem.wait("visible", timeout=self.WAIT_TIMEOUT)
            return elem
        except Exception as e:
            raise PhoneLinkAutomationError(
                f"Nie moge znalezc elementu: {title} ({control_type}). "
                f"Sprawdz czy Phone Link jest otwarty i widoczny."
            ) from e

    def _find_element_by_type(self, control_type: str, occurrence: int = 1):
        """Find a UI element by control type and occurrence number."""
        try:
            elem = self._main_window.child_window(
                control_type=control_type, found_index=occurrence - 1
            )
            elem.wait("visible", timeout=self.WAIT_TIMEOUT)
            return elem
        except Exception as e:
            raise PhoneLinkAutomationError(
                f"Nie moge znalezc elementu typu {control_type} (#{occurrence})."
            ) from e

    def _click_element(self, title: str, control_type: str) -> None:
        """Find and click a UI element."""
        elem = self._find_element(title, control_type)
        elem.click_input()
        time.sleep(0.3)
```

- [ ] **Step 3: Commit**

```bash
git add automation/phone_link.py
git commit -m "feat: PhoneLinkSender with pywinauto UIA automation"
```

---

### Task 7: Wire PhoneLinkSender into SMSSender Interface

**Files:**
- Modify: `core/sender.py`
- Modify: `automation/phone_link.py`

- [ ] **Step 1: Add SMSSender implementation to PhoneLinkSender**

Add to the end of `core/sender.py`:
```python
from automation.phone_link import PhoneLinkSender as _PhoneLinkAutomation


class PhoneLinkSender(SMSSender):
    def __init__(self, on_log=None):
        self._automation = _PhoneLinkAutomation(on_log=on_log)

    def send(self, numbers: list[str], message: str) -> None:
        self._automation.send_batch(numbers, message)

    def is_available(self) -> bool:
        return self._automation.is_available()
```

- [ ] **Step 2: Run existing tests to verify nothing broke**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add core/sender.py
git commit -m "feat: wire PhoneLinkSender into SMSSender interface"
```

---

### Task 8: GUI — Main Window Layout

**Files:**
- Create: `gui/app.py`

- [ ] **Step 1: Implement the full GUI layout**

`gui/app.py`:
```python
import os
import threading
import random
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.excel_importer import import_from_excel, import_from_csv
from core.batch_manager import BatchManager
from core.sender import PhoneLinkSender


class SMSSenderApp:
    MAX_SMS_CHARS = 160

    def __init__(self):
        self._root = tk.Tk()
        self._root.title("SMS Sender")
        self._root.geometry("550x650")
        self._root.resizable(False, False)

        self._numbers: list[str] = []
        self._skipped: list[dict] = []
        self._batch_manager: BatchManager | None = None
        self._sender = PhoneLinkSender(on_log=self._log)
        self._sending = False
        self._stop_requested = False

        self._build_ui()

    def run(self):
        self._root.mainloop()

    # ── UI Construction ──────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}

        # Import section
        import_frame = tk.Frame(self._root)
        import_frame.pack(fill="x", **pad)

        self._btn_import = tk.Button(
            import_frame, text="Importuj Excel", command=self._on_import
        )
        self._btn_import.pack(side="left")

        self._lbl_file = tk.Label(import_frame, text="Brak pliku", fg="gray")
        self._lbl_file.pack(side="left", padx=(10, 0))

        self._lbl_summary = tk.Label(self._root, text="", anchor="w")
        self._lbl_summary.pack(fill="x", **pad)

        # Number list
        list_frame = tk.LabelFrame(self._root, text="Numery")
        list_frame.pack(fill="both", expand=True, **pad)

        self._number_list = tk.Listbox(list_frame, height=8)
        scrollbar = tk.Scrollbar(list_frame, command=self._number_list.yview)
        self._number_list.config(yscrollcommand=scrollbar.set)
        self._number_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Message section
        tk.Label(self._root, text="Tresc SMS:", anchor="w").pack(fill="x", **pad)

        self._txt_message = tk.Text(self._root, height=3, wrap="word")
        self._txt_message.pack(fill="x", **pad)
        self._txt_message.bind("<KeyRelease>", self._on_message_changed)

        self._lbl_chars = tk.Label(self._root, text="Znaki: 0/160", anchor="w")
        self._lbl_chars.pack(fill="x", **pad)

        # Batch info
        self._lbl_batches = tk.Label(self._root, text="", anchor="w")
        self._lbl_batches.pack(fill="x", **pad)

        # Buttons
        btn_frame = tk.Frame(self._root)
        btn_frame.pack(fill="x", **pad)

        self._btn_send = tk.Button(
            btn_frame, text="▶ Wyslij", command=self._on_send, state="disabled"
        )
        self._btn_send.pack(side="left", padx=(0, 5))

        self._btn_stop = tk.Button(
            btn_frame, text="⏹ Stop", command=self._on_stop, state="disabled"
        )
        self._btn_stop.pack(side="left", padx=(0, 5))

        self._btn_resume = tk.Button(
            btn_frame, text="↻ Wznow", command=self._on_resume, state="disabled"
        )
        self._btn_resume.pack(side="left")

        # Progress bar
        self._progress = ttk.Progressbar(self._root, mode="determinate")
        self._progress.pack(fill="x", **pad)

        self._lbl_progress = tk.Label(self._root, text="", anchor="w")
        self._lbl_progress.pack(fill="x", **pad)

        # Log
        log_frame = tk.LabelFrame(self._root, text="Log")
        log_frame.pack(fill="both", expand=True, **pad)

        self._txt_log = tk.Text(log_frame, height=6, state="disabled", wrap="word")
        self._txt_log.pack(fill="both", expand=True)

    # ── Event Handlers ───────────────────────────────────────────

    def _on_import(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return

        try:
            if path.lower().endswith(".csv"):
                self._numbers, self._skipped = import_from_csv(path)
            else:
                self._numbers, self._skipped = import_from_excel(path)
        except FileNotFoundError as e:
            messagebox.showerror("Blad", str(e))
            return
        except Exception as e:
            messagebox.showerror("Blad odczytu pliku", str(e))
            return

        # Update UI
        filename = os.path.basename(path)
        self._lbl_file.config(text=f"plik: {filename}", fg="black")
        self._lbl_summary.config(
            text=f"Zaladowano: {len(self._numbers)} numerow ({len(self._skipped)} pominietych)"
        )

        self._number_list.delete(0, "end")
        for num in self._numbers:
            self._number_list.insert("end", f"{num}  ✓")
        for entry in self._skipped:
            self._number_list.insert("end", f"{entry['value']}  ✗ ({entry['reason']})")

        self._batch_manager = BatchManager(self._numbers, batch_size=20)
        self._update_batch_info()
        self._btn_send.config(state="normal" if self._numbers else "disabled")
        self._log(f"Zaimportowano {len(self._numbers)} numerow z {filename}")

    def _on_message_changed(self, event=None):
        text = self._txt_message.get("1.0", "end-1c")
        count = len(text)
        self._lbl_chars.config(
            text=f"Znaki: {count}/{self.MAX_SMS_CHARS}",
            fg="red" if count > self.MAX_SMS_CHARS else "black",
        )

    def _on_send(self):
        message = self._txt_message.get("1.0", "end-1c").strip()
        if not message:
            messagebox.showwarning("Brak tresci", "Wpisz tresc SMS-a")
            return
        if not self._numbers:
            messagebox.showwarning("Brak numerow", "Zaimportuj numery z Excela")
            return

        if len(self._numbers) > 40:
            if not messagebox.askyesno(
                "Ostrzezenie",
                "Wysylanie duzej liczby SMS-ow z prywatnego numeru moze "
                "triggerowac filtry anty-spam operatora. Kontynuowac?",
            ):
                return

        self._batch_manager = BatchManager(self._numbers, batch_size=20)
        self._start_sending(message)

    def _on_stop(self):
        self._stop_requested = True
        self._log("Zatrzymywanie wysylki...")

    def _on_resume(self):
        message = self._txt_message.get("1.0", "end-1c").strip()
        if not message:
            messagebox.showwarning("Brak tresci", "Wpisz tresc SMS-a")
            return
        self._start_sending(message)

    # ── Sending Logic ────────────────────────────────────────────

    def _start_sending(self, message: str):
        self._sending = True
        self._stop_requested = False
        self._btn_send.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._btn_resume.config(state="disabled")
        self._btn_import.config(state="disabled")

        messagebox.showwarning(
            "Uwaga",
            "Nie ruszaj myszka ani klawiatura podczas wysylki.\n"
            "Komputer bedzie zablokowany na czas automatyzacji.",
        )

        thread = threading.Thread(target=self._send_loop, args=(message,), daemon=True)
        thread.start()

    def _send_loop(self, message: str):
        bm = self._batch_manager
        total = bm.total_batches

        self._root.after(0, lambda: self._progress.config(maximum=total, value=0))

        try:
            self._sender._automation.connect()
        except Exception as e:
            self._log(f"BLAD: {e}")
            self._root.after(0, self._on_sending_done)
            return

        while True:
            idx = bm.next_pending_index()
            if idx is None or self._stop_requested:
                break

            batch = bm.get_batch(idx)
            self._log(f"Paczka {idx + 1}/{total} ({len(batch)} numerow)...")
            self._root.after(
                0, lambda i=idx: self._lbl_progress.config(text=f"Paczka {i + 1}/{total}")
            )

            try:
                self._sender.send(batch, message)
                bm.mark_sent(idx)
                self._log(f"Paczka {idx + 1}/{total} wyslana")
            except Exception as e:
                bm.mark_error(idx, str(e))
                self._log(f"BLAD paczka {idx + 1}/{total}: {e}")
                self._root.after(0, self._on_sending_done)
                return

            self._root.after(0, lambda i=idx: self._progress.config(value=i + 1))

            # Random delay between batches
            if bm.next_pending_index() is not None:
                delay = random.uniform(4.0, 8.0)
                self._log(f"Czekam {delay:.1f}s przed nastepna paczka...")
                time.sleep(delay)

        summary = bm.summary()
        self._log(
            f"Zakonczono: {summary['sent']} wyslanych, "
            f"{summary['error']} bledow, {summary['pending']} oczekujacych"
        )
        self._root.after(0, self._on_sending_done)

    def _on_sending_done(self):
        self._sending = False
        self._btn_send.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._btn_import.config(state="normal")

        if self._batch_manager:
            summary = self._batch_manager.summary()
            if summary["error"] > 0 or summary["pending"] > 0:
                self._btn_resume.config(state="normal")

    # ── Helpers ──────────────────────────────────────────────────

    def _update_batch_info(self):
        if not self._batch_manager or self._batch_manager.total_batches == 0:
            self._lbl_batches.config(text="")
            return
        bm = self._batch_manager
        sizes = [len(bm.get_batch(i)) for i in range(bm.total_batches)]
        self._lbl_batches.config(
            text=f"Paczki: {' + '.join(str(s) for s in sizes)} = {len(self._numbers)} numerow"
        )

    def _log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"{timestamp} {message}\n"

        def _append():
            self._txt_log.config(state="normal")
            self._txt_log.insert("end", line)
            self._txt_log.see("end")
            self._txt_log.config(state="disabled")

        if threading.current_thread() is threading.main_thread():
            _append()
        else:
            self._root.after(0, _append)
```

- [ ] **Step 2: Test that the app launches (manual)**

Run: `cd C:\Users\sadza\PycharmProjects\sms-sender && python main.py`
Expected: Window appears with the full layout. Close it manually.

- [ ] **Step 3: Commit**

```bash
git add gui/app.py main.py
git commit -m "feat: complete tkinter GUI with send/stop/resume workflow"
```

---

### Task 9: Integration Test — Full Manual Walkthrough

**Files:** None (manual testing only)

- [ ] **Step 1: Create a test Excel file**

Create `test_data.xlsx` with these numbers in column A:
- `+48512345678`
- `601234567`
- `48701234567`
- `abc` (invalid — should be skipped)
- (empty row — should be skipped)

- [ ] **Step 2: Run the app and test import**

Run: `python main.py`
1. Click "Importuj Excel" → select `test_data.xlsx`
2. Verify: "Zaladowano: 3 numerow (2 pominietych)"
3. Verify number list shows 3 ✓ and 2 ✗

- [ ] **Step 3: Test message composition**

1. Type a message longer than 160 chars → verify counter turns red
2. Type a short message → verify counter is black

- [ ] **Step 4: Test sending with Phone Link**

1. Open Phone Link and connect your Android phone
2. Type a short test message
3. Click "Wyslij"
4. Observe: automation opens Phone Link, adds recipients, pastes message, clicks send
5. If errors occur, note which element names need adjusting in `automation/phone_link.py`

- [ ] **Step 5: Adjust UIA selectors if needed**

The element names (`"Messages"`, `"New message"`, `"To"`, `"Send"`) are best guesses based on the English version of Phone Link. If your Phone Link is in Polish, you may need to change them. Use Inspect.exe (Windows SDK) to find the correct control names.

Run to discover element names:
```python
from pywinauto import Desktop
desktop = Desktop(backend="uia")
win = desktop.window(title_re=".*Phone Link.*")
win.print_control_identifiers()
```

Update `automation/phone_link.py` with the correct element names.

- [ ] **Step 6: Commit any selector adjustments**

```bash
git add automation/phone_link.py
git commit -m "fix: adjust UIA selectors for local Phone Link UI"
```

---

### Task 10: Final Polish

**Files:**
- Create: `README.md`

- [ ] **Step 1: Run all automated tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 2: Create README**

`README.md`:
```markdown
# SMS Sender

Aplikacja desktopowa do wysylania SMS-ow z komputera przez Windows Phone Link.

## Wymagania

- Windows 10/11 z zainstalowanym Phone Link
- Telefon Android polaczony przez Phone Link
- Python 3.12+

## Instalacja

```bash
pip install -r requirements.txt
```

## Uzycie

```bash
python main.py
```

1. Kliknij "Importuj Excel" i wybierz plik .xlsx lub .csv z numerami telefonow w kolumnie A
2. Wpisz tresc SMS-a
3. Kliknij "Wyslij"

**Wazne:** Nie ruszaj myszka ani klawiatura podczas wysylki.

## Formaty numerow

Akceptowane formaty: `+48512345678`, `48512345678`, `512345678`

## Limity

- Max 20 odbiorcow na paczke (limit Phone Link)
- Losowe opoznienie 4-8s miedzy paczkami
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with usage instructions"
```
