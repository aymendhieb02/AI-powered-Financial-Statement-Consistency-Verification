from __future__ import annotations

import re


SECTION_PATTERNS = {
    "bilan": r"\bBILAN\b",
    "etat_resultat": r"ETAT\s+DE\s+RESULTAT",
    "etat_variation_actif_net": r"ETAT\s+DE\s+VARIATION\s+DE\s+L'?ACTIF\s+NET",
    "notes": r"\bNOTES?\b",
    "rapport_general": r"RAPPORT\s+GENERAL",
    "rapport_special": r"RAPPORT\s+SPECIAL",
}


def detect_sections(text: str) -> dict[str, str]:
    matches: list[tuple[int, str]] = []
    for name, pattern in SECTION_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matches.append((match.start(), name))
    matches.sort()
    sections: dict[str, str] = {}
    for index, (start, name) in enumerate(matches):
        end = matches[index + 1][0] if index + 1 < len(matches) else len(text)
        sections[name] = text[start:end]
    return sections
