"""Transaction and transfer models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .wallet import Chain


class TokenTransfer(BaseModel):
    token_address: str
    token_symbol: str
    decimals: int
    amount_raw: str
    amount_decimal: float
    value_usd: Optional[float] = None


class Transaction(BaseModel):
    hash: str
    chain: Chain
    block: int
    timestamp: datetime
    from_address: str
    to_address: Optional[str] = None
    value: float  # native token amount
    value_usd: Optional[float] = None
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    method_id: Optional[str] = None
    decoded_method: Optional[str] = None
    token_transfers: list[TokenTransfer] = []
    is_success: bool = True


class Transfer(BaseModel):
    """Single value movement (native or ERC-20)."""
    tx_hash: str
    chain: Chain
    block: int
    timestamp: datetime
    from_address: str
    to_address: str
    value: float
    value_usd: Optional[float] = None
    token_symbol: Optional[str] = None  # None = native token


class Edge(BaseModel):
    """Graph edge between two wallets."""
    src: str
    dst: str
    chain: Chain
    tx_hash: str
    block: int
    timestamp: datetime
    value: float
    value_usd: Optional[float] = None
    token: Optional[str] = None
