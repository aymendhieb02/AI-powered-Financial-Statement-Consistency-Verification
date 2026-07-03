from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


def _simple_yaml(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    rules: list[dict[str, Any]] = []
    mandatory: list[str] = []
    current: dict[str, Any] | None = None
    in_mandatory = False
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "mandatory_fields:":
            in_mandatory = True
            current = None
            continue
        if line.startswith("- id:"):
            current = {"id": line.split(":", 1)[1].strip()}
            rules.append(current)
            in_mandatory = False
            continue
        if line.startswith("-") and in_mandatory:
            mandatory.append(line[1:].strip())
            continue
        if current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()
    return {"rules": rules, "mandatory_fields": mandatory}


class RuleLoader:
    def __init__(self, rules_dir: Path = Path("config/rules")) -> None:
        self.rules_dir = rules_dir

    def load(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"rules": [], "mandatory_fields": []}
        for path in sorted(self.rules_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) if yaml else _simple_yaml(path)
            payload["rules"].extend(data.get("rules", []))
            payload["mandatory_fields"].extend(data.get("mandatory_fields", []))
        return payload
