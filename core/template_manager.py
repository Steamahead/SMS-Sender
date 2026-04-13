import json
import os


class TemplateManager:
    """Manages saved SMS templates as a JSON file."""

    def __init__(self, path: str):
        self._path = path
        self._templates: dict[str, str] = {}
        self._load_from_disk()

    def save(self, name: str, content: str) -> None:
        self._templates[name] = content
        self._save_to_disk()

    def load(self, name: str) -> str | None:
        return self._templates.get(name)

    def delete(self, name: str) -> None:
        self._templates.pop(name, None)
        self._save_to_disk()

    def list_names(self) -> list[str]:
        return sorted(self._templates.keys())

    def _load_from_disk(self) -> None:
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                self._templates = json.load(f)

    def _save_to_disk(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._templates, f, ensure_ascii=False, indent=2)
