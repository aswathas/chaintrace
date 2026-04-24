"""Hack Tracer models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel

from .wallet import Chain


class Terminal(str, Enum):
    cex = "cex"
    mixer = "mixer"
    bridge = "bridge"
    cold = "cold"
    dead_end = "dead_end"


class TraceRequest(BaseModel):
    seed_address: str
    chain: Chain
    max_hops: int = 10
    min_value_usd: float = 100.0
    label: Optional[str] = None  # optional incident name


class TraceJob(BaseModel):
    job_id: str
    status: str  # queued / running / done / failed
    request: TraceRequest
    created_at: datetime
    completed_at: Optional[datetime] = None


class TraceNode(BaseModel):
    address: str
    chain: Chain
    depth: int
    labels: List[str] = []
    risk_score: Optional[float] = None
    terminal: Optional[Terminal] = None
    is_contract: bool = False


class TraceEdge(BaseModel):
    src: str
    dst: str
    chain: Chain
    tx_hash: str
    block: int
    timestamp: datetime
    value: float
    value_usd: Optional[float] = None
    token: Optional[str] = None
    is_bridge_hop: bool = False


class TraceResult(BaseModel):
    job_id: str
    seed: str
    chain: Chain
    nodes: List[TraceNode]
    edges: List[TraceEdge]
    terminals: Dict[str, Terminal]  # address → terminal type
    total_value_usd: Optional[float] = None
    hops_explored: int
    completed_at: datetime
    stale: bool = False  # True if result came from cache with exhausted providers
