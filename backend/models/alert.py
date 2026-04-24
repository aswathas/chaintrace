"""Alert rule and event models."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .wallet import Chain


class AlertRule(BaseModel):
    rule_id: str
    address: str
    chain: Chain
    min_value_usd: float = 0.0
    label_filter: Optional[str] = None  # alert only if counterparty has this label
    discord_webhook: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    created_at: datetime
    active: bool = True


class AlertEvent(BaseModel):
    event_id: str
    rule_id: str
    address: str
    chain: Chain
    tx_hash: str
    counterparty: str
    value_usd: float
    labels: List[str] = []
    triggered_at: datetime
    notified: bool = False
