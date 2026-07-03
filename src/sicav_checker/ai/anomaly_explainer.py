from __future__ import annotations

from sicav_checker.ai.ollama_client import ask_ollama
from sicav_checker.models import ComparisonResult


def explain_anomaly(result: ComparisonResult) -> str | None:
    prompt = (
        "Explain this SICAV audit anomaly for an expert accountant. "
        "Do not recalculate numbers; only explain likely document or labeling causes.\n"
        f"{result.model_dump(mode='json')}"
    )
    return ask_ollama(prompt)
