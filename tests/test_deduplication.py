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


class TestDeduplicateWithRows:
    def test_rows_stay_aligned_after_a_duplicate(self):
        from core.excel_importer import deduplicate_with_rows
        numbers = ["+48111111111", "+48111111111", "+48222222222"]
        rows = [["Anna"], ["Anna-dubel"], ["Jan"]]
        unique, unique_rows, removed = deduplicate_with_rows(numbers, rows)
        assert unique == ["+48111111111", "+48222222222"]
        assert unique_rows == [["Anna"], ["Jan"]]
        assert removed == 1
