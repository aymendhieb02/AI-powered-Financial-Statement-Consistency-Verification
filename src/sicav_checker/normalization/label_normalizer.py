from __future__ import annotations

import re
import unicodedata

try:
    from unidecode import unidecode
except ImportError:
    def unidecode(value: str) -> str:
        return "".join(
            char for char in unicodedata.normalize("NFKD", value)
            if not unicodedata.combining(char)
        )


def normalize_label(label: str) -> str:
    text = unidecode(label or "").lower()
    text = text.replace("&", " et ")
    text = re.sub(r"['\u2019]", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [token for token in text.split() if token not in {"de", "du", "des", "d", "l", "la", "le", "les"}]
    return "_".join(tokens)