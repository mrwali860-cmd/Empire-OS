"""Normalized opportunity candidate contract for source adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class OpportunityCandidate:
    """Source-independent representation of a discovered opportunity."""

    id: str
    source: str
    title: str
    description: str = ""
    url: str = ""
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("OpportunityCandidate.id must not be empty")
        if not self.source.strip():
            raise ValueError("OpportunityCandidate.source must not be empty")
        if not self.title.strip():
            raise ValueError("OpportunityCandidate.title must not be empty")
