from __future__ import annotations

from sicav_checker.chart_of_accounts.label_dictionary import LabelDictionary
from sicav_checker.chart_of_accounts.matching_engine import MatchingEngine
from sicav_checker.models import MatchMetadata
from sicav_checker.normalization.label_normalizer import normalize_label


class CanonicalMapper:
    def __init__(self, dictionary: LabelDictionary | None = None, matcher: MatchingEngine | None = None) -> None:
        self.dictionary = dictionary or LabelDictionary()
        self.matcher = matcher or MatchingEngine()

    def map_label(self, label: str, existing_canonicals: list[str] | None = None) -> MatchMetadata:
        normalized = normalize_label(label)
        alias = self.dictionary.lookup(label) or self.dictionary.lookup(normalized)
        if alias:
            return MatchMetadata(original_label=label, canonical_label=alias, confidence=1.0, method="alias_dictionary")
        if existing_canonicals:
            match, confidence, method = self.matcher.match(normalized, existing_canonicals)
            if match and confidence >= 0.88:
                return MatchMetadata(original_label=label, canonical_label=match, confidence=confidence, method=method)
        return MatchMetadata(original_label=label, canonical_label=normalized, confidence=0.95, method="normalized")
