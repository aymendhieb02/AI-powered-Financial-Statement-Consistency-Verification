from __future__ import annotations

from pathlib import Path

try:
    from loguru import logger
except ImportError:
    class _Logger:
        def warning(self, message: str, *args: object) -> None:
            print("WARNING: " + message.format(*args))
    logger = _Logger()


def extract_with_ocr(path: str | Path) -> str:
    logger.warning("OCR fallback is optional and not enabled for {}", Path(path))
    return ""