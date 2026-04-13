import json
import os


_DEFAULTS = {
    "last_import_dir": "",
    "batch_size": 20,
    "window_width": 900,
    "window_height": 700,
    "window_x": -1,
    "window_y": -1,
    "last_template": "",
}


class Settings:
    """Persists user settings to a JSON file."""

    def __init__(self, path: str):
        self._path = path
        self._data = dict(_DEFAULTS)
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                stored = json.load(f)
            self._data.update(stored)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def _set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()

    @property
    def last_import_dir(self) -> str:
        return self._data["last_import_dir"]

    @last_import_dir.setter
    def last_import_dir(self, value: str) -> None:
        self._set("last_import_dir", value)

    @property
    def batch_size(self) -> int:
        return self._data["batch_size"]

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        self._set("batch_size", value)

    @property
    def window_width(self) -> int:
        return self._data["window_width"]

    @window_width.setter
    def window_width(self, value: int) -> None:
        self._set("window_width", value)

    @property
    def window_height(self) -> int:
        return self._data["window_height"]

    @window_height.setter
    def window_height(self, value: int) -> None:
        self._set("window_height", value)

    @property
    def window_x(self) -> int:
        return self._data["window_x"]

    @window_x.setter
    def window_x(self, value: int) -> None:
        self._set("window_x", value)

    @property
    def window_y(self) -> int:
        return self._data["window_y"]

    @window_y.setter
    def window_y(self, value: int) -> None:
        self._set("window_y", value)

    @property
    def last_template(self) -> str:
        return self._data["last_template"]

    @last_template.setter
    def last_template(self, value: str) -> None:
        self._set("last_template", value)
