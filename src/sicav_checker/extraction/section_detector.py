from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher


SECTION_ORDER = (
    "bilan",
    "etat_resultat",
    "etat_variation_actif_net",
    "notes",
    "rapport_general",
    "rapport_special",
)

HEADING_LABELS = {
    "bilan": ("BILAN", "BILAN ARRETE AU 31 DECEMBRE", "BILAN AU 31 DECEMBRE"),
    "etat_resultat": ("ETAT DE RESULTAT", "ETAT DES RESULTATS"),
    "etat_variation_actif_net": ("ETAT DE VARIATION DE L ACTIF NET", "VARIATION DE L ACTIF NET"),
    "notes": ("NOTES AUX ETATS FINANCIERS", "NOTES AUX ETATS FINANCIER", "NOTES"),
    "rapport_general": ("RAPPORT GENERAL", "RAPPORT GENERAL DU COMMISSAIRE"),
    "rapport_special": ("RAPPORT SPECIAL", "RAPPORT SPECIAL DU COMMISSAIRE"),
}


@dataclass(frozen=True)
class SectionCandidate:
    key: str
    offset: int
    line: str
    normalized: str
    score: float


def normalize_heading_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return " ".join(text.split())


def detect_sections(text: str) -> dict[str, str]:
    candidates = detect_section_candidates(text)
    sections: dict[str, str] = {}
    for index, candidate in enumerate(candidates):
        end = candidates[index + 1].offset if index + 1 < len(candidates) else len(text)
        if candidate.key not in sections:
            sections[candidate.key] = text[candidate.offset:end].strip()
    return sections


def detect_section_candidates(text: str) -> list[SectionCandidate]:
    line_offsets = _line_offsets(text)
    candidates: list[SectionCandidate] = []
    seen: set[str] = set()
    for offset, line in line_offsets:
        normalized = normalize_heading_text(line)
        if not normalized:
            continue
        match = _match_heading(normalized)
        if match is None:
            continue
        key, score = match
        if key in seen:
            continue
        candidates.append(SectionCandidate(key=key, offset=offset, line=line.strip(), normalized=normalized, score=score))
        seen.add(key)
    candidates.sort(key=lambda item: item.offset)
    return _enforce_document_order(candidates)


def candidate_heading_lines(text: str) -> list[str]:
    candidates: list[str] = []
    for _, line in _line_offsets(text):
        normalized = normalize_heading_text(line)
        if any(token in normalized for token in ("BILAN", "ETAT", "NOTE", "RAPPORT", "ACTIF NET")):
            candidates.append(line.strip())
    return candidates[:50]


def _line_offsets(text: str) -> list[tuple[int, str]]:
    offsets: list[tuple[int, str]] = []
    cursor = 0
    for line in text.splitlines(keepends=True):
        offsets.append((cursor, line.rstrip("\r\n")))
        cursor += len(line)
    return offsets


def _match_heading(normalized: str) -> tuple[str, float] | None:
    best_key = ""
    best_score = 0.0
    for key, labels in HEADING_LABELS.items():
        for label in labels:
            if normalized == label or normalized.startswith(label + " "):
                return key, 1.0
            if label in normalized and _line_is_heading_like(normalized, label):
                return key, 0.96
            score = SequenceMatcher(None, normalized, label).ratio()
            if score > best_score:
                best_key = key
                best_score = score
    if best_score >= 0.86 and _line_is_heading_like(normalized, normalized):
        return best_key, best_score
    return None


def _line_is_heading_like(normalized: str, label: str) -> bool:
    if len(normalized.split()) > max(9, len(label.split()) + 4):
        return False
    return True


def _enforce_document_order(candidates: list[SectionCandidate]) -> list[SectionCandidate]:
    ordered: list[SectionCandidate] = []
    last_index = -1
    for candidate in candidates:
        index = SECTION_ORDER.index(candidate.key)
        if index >= last_index:
            ordered.append(candidate)
            last_index = index
    return ordered
