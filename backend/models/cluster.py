"""Entity clustering models."""
from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel


class ClusterHeuristic(str, Enum):
    common_funder = "common_funder"
    behavioral_fingerprint = "behavioral_fingerprint"
    nonce_linked = "nonce_linked"
    co_spend = "co_spend"


class ClusterEdge(BaseModel):
    src: str
    dst: str
    heuristic: ClusterHeuristic
    confidence: float  # 0–1
    evidence: str = ""


class ClusterResult(BaseModel):
    seed: str
    cluster_id: str
    members: List[str]
    edges: List[ClusterEdge]
    min_confidence: float = 0.6
