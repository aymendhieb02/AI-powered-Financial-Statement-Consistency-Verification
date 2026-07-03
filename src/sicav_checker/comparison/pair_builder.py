from __future__ import annotations


def build_valid_pairs(years: list[int] | set[int]) -> list[tuple[int, int]]:
    available = sorted(set(years))
    lookup = set(available)
    return [(year, year + 1) for year in available if year + 1 in lookup]
