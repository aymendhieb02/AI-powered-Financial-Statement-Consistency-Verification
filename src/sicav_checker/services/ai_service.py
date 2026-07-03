from __future__ import annotations

from sicav_checker.ai.anomaly_explainer import explain_anomaly
from sicav_checker.domain.models import ComparisonResult


class AIService:
    """Optional AI facade. It never performs numerical calculations."""

    def explain_anomaly(self, result: ComparisonResult) -> str | None:
        return explain_anomaly(result)