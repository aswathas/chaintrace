"""Wallet Profiler models."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .wallet import Chain


class RiskSignal(BaseModel):
    name: str
    weight: float
    detail: Optional[str] = None


class RiskScore(BaseModel):
    score: float  # 0–100, clamped
    tier: str  # low / medium / high / critical
    signals: List[RiskSignal]


class Counterparty(BaseModel):
    address: str
    chain: Chain
    labels: List[str] = []
    tx_count: int
    total_value_usd: float
    risk_score: Optional[float] = None


class ProfileResult(BaseModel):
    address: str
    chain: Chain
    risk: RiskScore
    counterparties: List[Counterparty] = []
    behavior_tags: List[str] = []
    profiled_at: datetime
    stale: bool = False
