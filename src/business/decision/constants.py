"""
constants.py

Empire OS
Decision Constants

Purpose:
Centralized constants used across the
Decision Engine.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

# ==========================================================
# Business Stages
# ==========================================================

BUSINESS_STAGE_STARTUP = "startup"
BUSINESS_STAGE_GROWTH = "growth"
BUSINESS_STAGE_SCALING = "scaling"
BUSINESS_STAGE_ENTERPRISE = "enterprise"

# ==========================================================
# Decision Categories
# ==========================================================

DECISION_GROWTH = "growth"
DECISION_REVENUE = "revenue"
DECISION_PROFIT = "profit"
DECISION_CLIENT = "client"
DECISION_PRODUCT = "product"
DECISION_RISK = "risk"
DECISION_AUTOMATION = "automation"
DECISION_GENERAL = "general"

# ==========================================================
# Urgency Levels
# ==========================================================

URGENCY_LOW = "low"
URGENCY_NORMAL = "normal"
URGENCY_HIGH = "high"
URGENCY_CRITICAL = "critical"

# ==========================================================
# Risk Levels
# ==========================================================

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"

# ==========================================================
# Confidence Levels
# ==========================================================

CONFIDENCE_LOW = 40
CONFIDENCE_MEDIUM = 60
CONFIDENCE_HIGH = 80
CONFIDENCE_VERY_HIGH = 95

# ==========================================================
# Business Score Weights
# ==========================================================

ROI_WEIGHT = 0.30

RISK_WEIGHT = 0.20

ALIGNMENT_WEIGHT = 0.20

BUSINESS_IMPACT_WEIGHT = 0.15

TIME_WEIGHT = 0.10

COST_WEIGHT = 0.05

# ==========================================================
# Decision Status
# ==========================================================

STATUS_PENDING = "pending"

STATUS_ANALYZING = "analyzing"

STATUS_RECOMMENDED = "recommended"

STATUS_APPROVED = "approved"

STATUS_REJECTED = "rejected"

STATUS_COMPLETED = "completed"

# ==========================================================
# Recommendation Types
# ==========================================================

PRIMARY_RECOMMENDATION = "primary"

SECONDARY_RECOMMENDATION = "secondary"

ALTERNATIVE_RECOMMENDATION = "alternative"

# ==========================================================
# Empire Rules
# ==========================================================

MAX_DECISION_OPTIONS = 10

MIN_CONFIDENCE_TO_RECOMMEND = 60

MAX_RISK_ALLOWED = "high"