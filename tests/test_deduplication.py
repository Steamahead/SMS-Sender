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
