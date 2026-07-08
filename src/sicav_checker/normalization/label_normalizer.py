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
    "total_actif": "total_actif",
    "total_des_actifs": "total_actif",
    "total_passif_actif_net": "total_passif_actif_net",
    "total_passif_et_actif_net": "total_passif_actif_net",
    "revenus_des_prises_en_pensions": "revenus_prises_pension",
    "revenus_prises_en_pensions": "revenus_prises_pension",
    "revenus_prises_en_pension": "revenus_prises_pension",
    "sommes_distribuables_exercice": "sommes_distribuables_exercice",
    "rafa_c_gularisation_sommes_non_distribuables": "regularisation_sommes_non_distribuables",
    "rafa_c_gularisation_sommes_distribuables": "regularisation_sommes_distribuables",
    "ra_c_gularisation_sommes_non_distribuables": "regularisation_sommes_non_distribuables",
    "ra_c_gularisation_sommes_distribuables": "regularisation_sommes_distribuables",
}

HEADER_PREFIX_PATTERNS = (
    re.compile(r"^\s*bilan\s+(?:arrete\s+)?(?:au\s+)?31\s+decembre\s+\d{4}\b"),
    re.compile(r"^\s*etat\s+(?:de\s+)?resultat\b"),
    re.compile(r"^\s*etat\s+de\s+variation\s+de\s+l\s+actif\s+net\b"),
    re.compile(r"^\s*note\s+(?:annee\s+\d{4}\s*){1,4}"),
    re.compile(r"^\s*annee\s+\d{4}(?:\s+annee\s+\d{4})*"),
    re.compile(r"^\s*(?:actif|passif)\s+note\b"),
    re.compile(r"^\s*montants\s+exprimes.*?tunisiens\b"),
    re.compile(r"^\s*des\s+operations\s+d\s+exploitation\b"),
)


def _repair_mojibake(value: str) -> str:
    if "\u00c3" not in value and "\u00c2" not in value:
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except UnicodeError:
        return value


def _strip_header_noise(text: str) -> str:
    text = text.replace("_", " ")
    text = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", " ", text)
    previous = None
    while text != previous:
        previous = text
        text = " ".join(text.split())
        for pattern in HEADER_PREFIX_PATTERNS:
            text = pattern.sub(" ", text).strip()
    return text


def normalize_label(label: str) -> str:
    text = unidecode(_repair_mojibake(label or "")).lower()
    text = text.replace("&", " et ")
    text = re.sub(r"[\x27\u2019]", " ", text)
    text = _strip_header_noise(text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [token for token in text.split() if token not in STOPWORDS]
    normalized = "_".join(tokens)
    return ALIASES.get(normalized, normalized)
