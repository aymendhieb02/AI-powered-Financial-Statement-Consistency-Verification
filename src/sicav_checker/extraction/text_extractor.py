from __future__ import annotations

from pathlib import Path

try:
    from loguru import logger
except ImportError:
    class _Logger:
        def warning(self, message: str, *args: object) -> None:
            print("WARNING: " + message.format(*args))
    logger = _Logger()


def extract_text(path: str | Path) -> tuple[str, str]:
    pdf_path = Path(path)
    try:
        import fitz

        with fitz.open(pdf_path) as doc:
            return "\n".join(page.get_text("text") for page in doc), "pymupdf"
    except Exception as exc:
        logger.warning("PyMuPDF failed for {}: {}", pdf_path, exc)

    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text, "pdfplumber"
    except Exception as exc:
        logger.warning("pdfplumber failed for {}: {}", pdf_path, exc)
        return "", "none"