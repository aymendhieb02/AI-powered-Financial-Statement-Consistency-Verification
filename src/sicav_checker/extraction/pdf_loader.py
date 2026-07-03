from __future__ import annotations

from pathlib import Path


def list_pdfs(raw_dir: str | Path) -> list[Path]:
    return sorted(Path(raw_dir).glob("*.pdf"))
