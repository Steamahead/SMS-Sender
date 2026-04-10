import os
import tempfile

import pytest
from openpyxl import Workbook

from core.excel_importer import (
    normalize_phone_number,
    validate_phone_number,
    import_from_excel,
    import_from_csv,
)


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
