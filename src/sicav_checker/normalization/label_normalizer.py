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


STOPWORDS = {"de", "du", "des", "d", "l", "la", "le", "les", "a", "au", "aux"}

ALIASES = {
    "total_actifs": "total_actif",
    "actif_total": "total_actif",
    "passif_total": "total_passif",
    "total_actif_net": "actif_net",
    "portefeuille_titre": "portefeuille_titres",
    "resultat_exercice": "resultat_net",
    "benefice_net": "resultat_net",
    "perte_nette": "resultat_net",
    "etat_variation_actif_net": "variation_actif_net",
    "nombre_titres": "nombre_actions",
}


def normalize_label(label: str) -> str:
    text = unidecode(label or "").lower()
    text = text.replace("&", " et ")
    text = re.sub(r"['\u2019]", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [token for token in text.split() if token not in STOPWORDS]
    normalized = "_".join(tokens)
    return ALIASES.get(normalized, normalized)
