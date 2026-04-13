import re


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
