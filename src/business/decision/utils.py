"""
utils.py

Empire OS
Decision Utilities

Purpose:
Reusable helper functions for the Decision Engine.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

# -------------------------------------------------
# Normalize Score
# -------------------------------------------------

def normalize_score(
    value: float,
    minimum: float,
    maximum: float
) -> float:
    """
    Normalize a value to 0–100.
    """

    if maximum <= minimum:
        return 0.0

    score = (
        (value - minimum)
        / (maximum - minimum)
    ) * 100

    return max(0.0, min(100.0, score))


# -------------------------------------------------
# Clamp Value
# -------------------------------------------------

def clamp(
    value: float,
    minimum: float,
    maximum: float
) -> float:
    """
    Keep value inside range.
    """

    return max(minimum, min(value, maximum))


# -------------------------------------------------
# Weighted Score
# -------------------------------------------------

def weighted_score(
    score: float,
    weight: float
) -> float:
    """
    Apply weight to score.
    """

    return score * weight


# -------------------------------------------------
# Calculate Average
# -------------------------------------------------

def average(
    values: list[float]
) -> float:
    """
    Calculate average.
    """

    if not values:
        return 0.0

    return sum(values) / len(values)


# -------------------------------------------------
# Sort Highest First
# -------------------------------------------------

def sort_descending(
    values: list
):
    """
    Sort highest first.
    """

    return sorted(
        values,
        reverse=True
    )


# -------------------------------------------------
# Percentage
# -------------------------------------------------

def percentage(
    part: float,
    total: float
) -> float:
    """
    Calculate percentage.
    """

    if total == 0:
        return 0.0

    return (part / total) * 100


# -------------------------------------------------
# Confidence Label
# -------------------------------------------------

def confidence_label(
    confidence: float
) -> str:
    """
    Convert confidence score
    into readable label.
    """

    if confidence >= 90:
        return "Very High"

    if confidence >= 75:
        return "High"

    if confidence >= 60:
        return "Medium"

    if confidence >= 40:
        return "Low"

    return "Very Low"


# -------------------------------------------------
# Safe Division
# -------------------------------------------------

def safe_divide(
    numerator: float,
    denominator: float
) -> float:
    """
    Prevent division by zero.
    """

    if denominator == 0:
        return 0.0

    return numerator / denominator