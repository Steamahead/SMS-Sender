import re

from core.sms_counter import strip_polish as _strip_polish


class Personalizer:
    """Substitutes {variable} placeholders in SMS templates with row data."""

    _VAR_RE = re.compile(r"\{(\w+)\}")

    def __init__(self, template: str, headers: list[str] | None):
        self._template = template
        self._headers = headers
        self._variables = self._VAR_RE.findall(template)

    @property
    def variables(self) -> list[str]:
        return self._variables

    def missing_variables(self) -> list[str]:
        """Return list of variables that cannot be mapped to columns."""
        available = self._available_names()
        return [v for v in self._variables if v not in available]

    def suggestion(self, name: str) -> str | None:
        """The column the user most likely meant: {imie} → "Imię"."""
        key = _loose(name)
        for header in self._headers or []:
            if header and _loose(header) == key:
                return header
        return None

    def render(self, row: list[str]) -> str:
        """Substitute variables in template with values from row data."""
        mapping = self._build_mapping(row)

        def replacer(match):
            name = match.group(1)
            return mapping.get(name, match.group(0))

        return self._VAR_RE.sub(replacer, self._template)

    def _available_names(self) -> set[str]:
        names = set()
        if self._headers:
            names.update(self._headers)
        for i in range(26):
            names.add(chr(65 + i))
        return names

    def _build_mapping(self, row: list[str]) -> dict[str, str]:
        mapping = {}
        for i, val in enumerate(row):
            if i < 26:
                mapping[chr(65 + i)] = val
        if self._headers:
            for i, header in enumerate(self._headers):
                if i < len(row):
                    mapping[header] = row[i]
        return mapping


def _loose(name: str) -> str:
    return _strip_polish(name).casefold()


def unresolved_variables(text: str) -> list[str]:
    """Placeholders still in a rendered text — they would reach the recipient as-is."""
    return Personalizer._VAR_RE.findall(text)


def render_for_numbers(template: str, headers: list[str] | None,
                       numbers: list[str], row_data: list[list],
                       strip_polish: bool = False) -> dict[str, str]:
    """The exact text each number will receive.

    ``row_data[i]`` belongs to ``numbers[i]``; a number with no row (typed in by
    hand) gets the template unchanged. ``strip_polish`` runs after substitution,
    so names from the file lose their diacritics too.
    """
    personalizer = Personalizer(template, headers) if template and row_data else None
    messages = {}
    for i, number in enumerate(numbers):
        if personalizer and i < len(row_data):
            text = personalizer.render(row_data[i])
        else:
            text = template
        messages[number] = _strip_polish(text) if strip_polish else text
    return messages
