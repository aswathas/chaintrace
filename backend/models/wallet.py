"""Wallet and address models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class Chain(str, Enum):
    eth = "eth"
    polygon = "polygon"
    arb = "arb"
    base = "base"
    bsc = "bsc"
    solana = "solana"


class Address(BaseModel):
    address: str
    chain: Chain


class Wallet(BaseModel):
    address: str
    chain: Chain
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    tx_count: int = 0
    balance_usd: float = 0.0
    labels: List[str] = []
    risk_score: Optional[float] = None
    is_contract: bool = False
    created_at_block: Optional[int] = None


class WalletProfile(BaseModel):
    wallet: Wallet
    risk_score: float
    risk_tier: str  # low / medium / high / critical
    top_counterparties: List[str] = []
    behavior_tags: List[str] = []
    profiled_at: datetime
