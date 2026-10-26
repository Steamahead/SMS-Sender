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


class TestSeveralNumbersInOneCell:
    def test_comma_separated_cell(self):
        valid, skipped = parse_clipboard_text("512 345 678, 600-700-800\n")
        assert valid == ["+48512345678", "+48600700800"]
        assert skipped == []

    def test_semicolon_separated_cell(self):
        valid, _ = parse_clipboard_text("512345678;600700800;+48 601 602 603")
        assert valid == ["+48512345678", "+48600700800", "+48601602603"]

    def test_cell_with_line_breaks_is_quoted_by_excel(self):
        # Alt+Enter inside a cell: Excel wraps the cell in quotes when copying.
        valid, _ = parse_clipboard_text('"512345678\n600700800"\n601602603\n')
        assert valid == ["+48512345678", "+48600700800", "+48601602603"]

    def test_every_number_in_a_row_is_taken(self):
        valid, _ = parse_clipboard_text("Anna\t512345678\t600700800\n")
        assert valid == ["+48512345678", "+48600700800"]

    def test_bad_fragment_is_reported_good_ones_kept(self):
        valid, skipped = parse_clipboard_text("512345678, 12345")
        assert valid == ["+48512345678"]
        assert [s["value"] for s in skipped] == ["12345"]
