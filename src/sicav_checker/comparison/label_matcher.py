from __future__ import annotations

import re
from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz, process
except ImportError:
    fuzz = None
    process = None


def _number_tokens(label: str) -> list[str]:
    return re.findall(r"\d+", label)


def _compatible_number_tokens(source: str, candidate: str) -> bool:
    source_numbers = _number_tokens(source)
    candidate_numbers = _number_tokens(candidate)
    return not source_numbers or not candidate_numbers or source_numbers == candidate_numbers


def match_label(canonical_label: str, candidates: list[str], threshold: int = 88) -> tuple[str | None, float, bool]:
    if canonical_label in candidates:
        return canonical_label, 100.0, False
    candidates = [candidate for candidate in candidates if _compatible_number_tokens(canonical_label, candidate)]
    if not candidates:
        return None, 0.0, False
    if process is None or fuzz is None:
        scored = [(candidate, SequenceMatcher(None, canonical_label, candidate).ratio() * 100) for candidate in candidates]
        match, score = max(scored, key=lambda item: item[1])
        if score >= threshold:
            return match, float(score), True
        return None, float(score), False
    result = process.extractOne(canonical_label, candidates, scorer=fuzz.token_sort_ratio)
    if result is None:
        return None, 0.0, False
    match, score, _ = result
    if score >= threshold:
        return match, float(score), True
    return None, float(score), False
