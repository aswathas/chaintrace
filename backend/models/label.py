"""Label and label-source models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class LabelSource(str, Enum):
    hardcoded = "hardcoded"
    community = "community"
    etherscan = "etherscan"
    arkham = "arkham"
    submission = "submission"
    heuristic = "heuristic"


class Label(BaseModel):
    address: str
    name: str
    category: str  # e.g. mixer / cex / bridge / defi / exploit
    source: LabelSource
    confidence: float = 1.0  # 0–1
    submitted_by: Optional[str] = None
    created_at: datetime
