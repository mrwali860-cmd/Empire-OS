"""
exceptions.py

Empire OS
Decision Exceptions

Purpose:
Defines all Decision Engine exceptions.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

# ==========================================================
# Base Exception
# ==========================================================

class DecisionEngineError(Exception):
    """
    Base exception for the Decision Engine.
    """


# ==========================================================
# Context Exceptions
# ==========================================================

class InvalidContextError(DecisionEngineError):
    """
    Raised when business context is invalid.
    """


class MissingGoalError(DecisionEngineError):
    """
    Raised when no business goal is provided.
    """


# ==========================================================
# Evaluation Exceptions
# ==========================================================

class EvaluationError(DecisionEngineError):
    """
    Raised during opportunity evaluation.
    """


class InvalidScoreError(DecisionEngineError):
    """
    Raised when calculated score is invalid.
    """


# ==========================================================
# Recommendation Exceptions
# ==========================================================

class RecommendationError(DecisionEngineError):
    """
    Raised when recommendation fails.
    """


class NoRecommendationFoundError(RecommendationError):
    """
    Raised when no suitable recommendation exists.
    """


# ==========================================================
# Ranking Exceptions
# ==========================================================

class RankingError(DecisionEngineError):
    """
    Raised when ranking fails.
    """


# ==========================================================
# Report Exceptions
# ==========================================================

class ReportGenerationError(DecisionEngineError):
    """
    Raised when report generation fails.
    """
