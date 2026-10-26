"""CSV files as Polish Excel writes them: semicolons, cp1250 or UTF-8 with BOM."""
import pytest

from core.excel_importer import (
    detect_phone_column_csv, get_column_headers_csv, import_from_csv, read_csv_rows,
)

CONTENT = "Imię;Telefon\nŁucja;512345678\nJan;600700800\n"


@pytest.fixture(params=["cp1250", "utf-8-sig", "utf-8"])
def polish_csv(tmp_path, request):
    path = tmp_path / "lista.csv"
    path.write_bytes(CONTENT.encode(request.param))
    return str(path)


def test_rows_are_split_on_semicolons_and_decoded(polish_csv):
    assert read_csv_rows(polish_csv)[1] == ["Łucja", "512345678"]


def test_headers_are_read_without_bom(polish_csv):
    assert get_column_headers_csv(polish_csv) == ["Imię", "Telefon"]


def test_phone_column_is_found(polish_csv):
    assert detect_phone_column_csv(polish_csv) == 1


def test_numbers_and_rows_are_imported(polish_csv):
    valid, _, rows = import_from_csv(polish_csv, column=1, return_rows=True)
    assert valid == ["+48512345678", "+48600700800"]
    assert rows[0] == ["Łucja", "512345678"]


def test_comma_files_still_work(tmp_path):
    path = tmp_path / "lista.csv"
    path.write_text("Imie,Telefon\nAnna,512345678\n", encoding="utf-8")
    assert read_csv_rows(str(path)) == [["Imie", "Telefon"], ["Anna", "512345678"]]
    assert get_column_headers_csv(str(path)) == ["Imie", "Telefon"]


def test_headerless_file_has_no_headers(tmp_path):
    path = tmp_path / "lista.csv"
    path.write_text("512345678\n600700800\n", encoding="utf-8")
    assert get_column_headers_csv(str(path)) is None


def test_csv_cell_with_several_numbers(tmp_path):
    path = tmp_path / "lista.csv"
    path.write_text('Imie;Telefon\nNowak;"512345678, 600700800"\n', encoding="utf-8")
    valid, _, rows = import_from_csv(str(path), column=1, return_rows=True)
    assert valid == ["+48512345678", "+48600700800"]
    assert len(rows) == 2
