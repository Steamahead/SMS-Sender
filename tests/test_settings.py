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
