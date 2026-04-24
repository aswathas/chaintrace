"""Behavioral fingerprint clustering — gas price + tx timing histogram similarity."""
from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from ..profiler.behavior import gas_price_fingerprint

COSINE_THRESHOLD = 0.9
TIMING_BINS = 24  # hourly bins for 24h period


@dataclass
class ClusterEdge:
    wallet_a: str
    wallet_b: str
    heuristic: str
    confidence: float
    evidence: str = ""


def _timing_histogram(txs: list[dict[str, Any]], bins: int = TIMING_BINS) -> list[float]:
    """Normalised hour-of-day distribution of transactions."""
    counts = [0] * bins
    for tx in txs:
        ts = tx.get("timestamp", 0)
        if ts:
            hour = (ts // 3600) % bins
            counts[hour] += 1
    total = sum(counts)
    if total == 0:
        return [0.0] * bins
    return [c / total for c in counts]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def find_fingerprint_clusters(
    wallet_txs: dict[str, list[dict[str, Any]]],
) -> list[ClusterEdge]:
    """Return edges for wallet pairs with cosine similarity ≥ 0.9 on their fingerprints.

    wallet_txs: {address: list_of_tx_dicts}
    Each tx dict must have: timestamp, gas_price_gwei.
    """
    # Precompute fingerprints
    fingerprints: dict[str, list[float]] = {}
    for addr, txs in wallet_txs.items():
        gas_vec = gas_price_fingerprint(txs, bins=20)
        timing_vec = _timing_histogram(txs)
        combined = gas_vec + timing_vec  # len 44
        fingerprints[addr.lower()] = combined

    edges: list[ClusterEdge] = []
    addrs = list(fingerprints.keys())

    for addr_a, addr_b in combinations(addrs, 2):
        sim = _cosine_similarity(fingerprints[addr_a], fingerprints[addr_b])
        if sim >= COSINE_THRESHOLD:
            edges.append(ClusterEdge(
                wallet_a=addr_a,
                wallet_b=addr_b,
                heuristic="behavioral_fingerprint",
                confidence=round(sim, 4),
                evidence=f"gas+timing cosine similarity {sim:.3f}",
            ))

    return edges
