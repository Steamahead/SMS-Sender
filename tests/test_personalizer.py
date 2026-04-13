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
