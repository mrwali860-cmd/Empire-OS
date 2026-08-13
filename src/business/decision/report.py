"""
report.py

Empire OS
Business Decision Report Engine
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .models import DecisionReport


class ReportEngine:
    """Builds a Founder-ready decision report."""

    def build(self, report: DecisionReport) -> dict[str, Any]:
        """Build a Founder-ready decision report."""
        recommended = report.recommended

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "business_goal": report.context.goal,
            "recommendation": recommended.option.title,
            "confidence": recommended.confidence,
            "business_score": recommended.score.final_score,
            "reasons": recommended.reasons,
            "risks": recommended.risks,
            "expected_results": recommended.expected_results,
            "alternatives": [
                alternative.option.title
                for alternative in report.alternatives
            ],
        }

    def export_json(self, report: DecisionReport) -> dict[str, Any]:
        """Export the complete decision report as a dictionary."""
        return asdict(report)

    def founder_summary(self, report: DecisionReport) -> str:
        """Generate a concise Founder-facing summary."""
        recommendation = report.recommended

        return (
            f"Recommendation: {recommendation.option.title}\n"
            f"Business Score: {recommendation.score.final_score}\n"
            f"Confidence: {recommendation.confidence}%"
        )