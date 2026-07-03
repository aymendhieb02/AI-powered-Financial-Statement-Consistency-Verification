from __future__ import annotations

from pathlib import Path
from typing import Any

from sicav_checker.normalization.label_normalizer import normalize_label

try:
    import yaml
except ImportError:
    yaml = None


class LabelDictionary:
    def __init__(self, path: Path = Path("config/chart_of_accounts.yaml")) -> None:
        self.path = path
        self.alias_to_canonical: dict[str, str] = {}
        self.load()

    def _add(self, alias: str, canonical: str) -> None:
        self.alias_to_canonical[alias.lower()] = canonical
        self.alias_to_canonical[normalize_label(alias).lower()] = canonical

    def load(self) -> None:
        if not self.path.exists():
            return
        if yaml:
            data: dict[str, Any] = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
            for item in data.get("concepts", []):
                canonical = item.get("canonical_name", "")
                self._add(canonical, canonical)
                for alias in item.get("aliases", []):
                    self._add(str(alias), canonical)
            return

        current = ""
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("- canonical_name:") or line.startswith("canonical_name:"):
                current = line.split(":", 1)[1].strip()
                self._add(current, current)
            elif line.startswith("-") and current:
                self._add(line[1:].strip(), current)

    def lookup(self, label: str) -> str | None:
        return self.alias_to_canonical.get(label.lower()) or self.alias_to_canonical.get(normalize_label(label).lower())