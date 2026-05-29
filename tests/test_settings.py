import os
import json
import tempfile

from core.settings import Settings
from core import crypto_store


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

    def test_api_key_roundtrip(self):
        path = os.path.join(tempfile.mkdtemp(), "settings.json")
        s1 = Settings(path)
        s1.gemini_api_key = "sk-ant-secret-123"
        s2 = Settings(path)
        assert s2.gemini_api_key == "sk-ant-secret-123"

    def test_api_key_not_plaintext_on_disk(self):
        if not crypto_store.is_available():
            return  # DPAPI unavailable — encryption is a no-op here
        path = os.path.join(tempfile.mkdtemp(), "settings.json")
        s = Settings(path)
        s.gemini_api_key = "sk-ant-secret-456"
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        assert raw["gemini_api_key"] != "sk-ant-secret-456"
        assert crypto_store.is_protected(raw["gemini_api_key"])

    def test_legacy_plaintext_key_is_migrated(self):
        if not crypto_store.is_available():
            return
        path = os.path.join(tempfile.mkdtemp(), "settings.json")
        # Simulate an old settings file with a plaintext key.
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"gemini_api_key": "old-plaintext-key"}, f)
        s = Settings(path)
        assert s.gemini_api_key == "old-plaintext-key"  # still readable
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        assert crypto_store.is_protected(raw["gemini_api_key"])  # now encrypted
