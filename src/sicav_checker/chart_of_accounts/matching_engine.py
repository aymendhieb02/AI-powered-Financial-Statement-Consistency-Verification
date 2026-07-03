from __future__ import annotations

from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz, process
except ImportError:
    fuzz = None
    process = None


class MatchingEngine:
    def match(self, label: str, candidates: list[str]) -> tuple[str | None, float, str]:
        if label in candidates:
            return label, 1.0, "exact"
        if not candidates:
            return None, 0.0, "none"
        if process and fuzz:
            result = process.extractOne(label, candidates, scorer=fuzz.token_sort_ratio)
            if result:
                match, score, _ = result
                return match, float(score) / 100, "rapidfuzz"
        match = max(candidates, key=lambda item: SequenceMatcher(None, label, item).ratio())
        score = SequenceMatcher(None, label, match).ratio()
        return match, score, "difflib"
