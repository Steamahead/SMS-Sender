from core.sms_counter import count_sms, MAX_CHARS


class TestEncoding:
    def test_plain_text_is_gsm(self):
        assert count_sms("Dzien dobry").encoding == "GSM"

    def test_polish_letter_forces_unicode(self):
        assert count_sms("Dzień dobry").encoding == "UCS-2"

    def test_extended_gsm_chars_count_double(self):
        # { } [ ] ~ \ ^ | and the euro sign take two GSM-7 slots each
        assert count_sms("{}").units == 4
        assert count_sms("€").units == 2


class TestParts:
    def test_empty_message_is_zero_parts(self):
        assert count_sms("").parts == 0

    def test_gsm_single_part_up_to_160(self):
        assert count_sms("a" * 160).parts == 1
        assert count_sms("a" * 161).parts == 2

    def test_gsm_multipart_uses_153_per_part(self):
        assert count_sms("a" * 306).parts == 2
        assert count_sms("a" * 307).parts == 3

    def test_unicode_single_part_up_to_70(self):
        assert count_sms("ą" * 70).parts == 1
        assert count_sms("ą" * 71).parts == 2

    def test_unicode_multipart_uses_67_per_part(self):
        assert count_sms("ą" * 134).parts == 2
        assert count_sms("ą" * 135).parts == 3

    def test_long_polish_message_is_many_parts_not_two(self):
        # The old counter said "2 SMS" for anything over 160 characters.
        assert count_sms("ż" * 700).parts == 11


def test_limit_is_700():
    assert MAX_CHARS == 700


class TestStripPolish:
    def test_polish_letters_become_plain(self):
        from core.sms_counter import strip_polish
        assert strip_polish("Zażółć gęślą jaźń ŁÓDŹ") == "Zazolc gesla jazn LODZ"

    def test_typographic_quotes_and_dashes_become_gsm(self):
        from core.sms_counter import strip_polish
        assert strip_polish("„Hej” – to ’test’…") == '"Hej" - to \'test\'...'

    def test_stripped_message_is_gsm_and_cheaper(self):
        from core.sms_counter import strip_polish
        text = "Zażółć gęślą jaźń. " * 36
        assert count_sms(text).parts == 11
        assert count_sms(strip_polish(text)).encoding == "GSM"
        assert count_sms(strip_polish(text)).parts == 5
