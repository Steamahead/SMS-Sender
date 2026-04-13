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
