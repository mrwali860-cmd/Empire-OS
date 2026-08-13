"""
scoring.py

Empire OS
Business Decision Scoring Engine

Purpose:
Calculate the business score for every
decision option.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

from .constants import (
    ALIGNMENT_WEIGHT,
    BUSINESS_IMPACT_WEIGHT,
    COST_WEIGHT,
    RISK_WEIGHT,
    ROI_WEIGHT,
    TIME_WEIGHT,
)
from .utils import (
    clamp,
    weighted_score,
)


class BusinessScoringEngine:
    """
    Empire Business Scoring Engine.
    """

    def calculate_final_score(
        self,
        *,
        roi: float,
        risk: float,
        alignment: float,
        impact: float,
        execution_time: float,
        cost: float,
    ) -> float:
        """
        Calculate the final business score.

        Every input should be normalized
        between 0 and 100.
        """

        roi = clamp(roi, 0, 100)

        risk = clamp(risk, 0, 100)

        alignment = clamp(alignment, 0, 100)

        impact = clamp(impact, 0, 100)

        execution_time = clamp(execution_time, 0, 100)

        cost = clamp(cost, 0, 100)

        score = (

            weighted_score(
                roi,
                ROI_WEIGHT,
            )

            +

            weighted_score(
                alignment,
                ALIGNMENT_WEIGHT,
            )

            +

            weighted_score(
                impact,
                BUSINESS_IMPACT_WEIGHT,
            )

            -

            weighted_score(
                risk,
                RISK_WEIGHT,
            )

            -

            weighted_score(
                execution_time,
                TIME_WEIGHT,
            )

            -

            weighted_score(
                cost,
                COST_WEIGHT,
            )

        )

        return round(
            clamp(score, 0, 100),
            2,
        )