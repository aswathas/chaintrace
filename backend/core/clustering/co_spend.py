"""Co-spend clustering — wallets appearing together as inputs/outputs in ≥3 txs."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Any

MIN_CO_APPEARANCES = 3


@dataclass
class ClusterEdge:
    wallet_a: str
    wallet_b: str
    heuristic: str
    confidence: float
    evidence: str = ""


def find_co_spend_clusters(
    multi_party_txs: list[dict[str, Any]],
) -> list[ClusterEdge]:
    """Find address pairs that co-appear in ≥3 transactions.

    multi_party_txs: list of {tx_hash: str, participants: list[str]}
    A participant is any address appearing as input or output in the tx.
    """
    # Count how many times each pair co-appears
    pair_count: dict[frozenset, int] = defaultdict(int)
    pair_tx_hashes: dict[frozenset, list[str]] = defaultdict(list)

    for tx in multi_party_txs:
        participants = [p.lower() for p in tx.get("participants", [])]
        tx_hash = tx.get("tx_hash", "")
        unique_participants = list(set(participants))
        for addr_a, addr_b in combinations(unique_participants, 2):
            pair = frozenset({addr_a, addr_b})
            pair_count[pair] += 1
            if tx_hash:
                pair_tx_hashes[pair].append(tx_hash)

    edges: list[ClusterEdge] = []
    for pair, count in pair_count.items():
        if count >= MIN_CO_APPEARANCES:
            addr_a, addr_b = sorted(pair)
            # Scale confidence: 3 co-appearances = 0.6, grows toward 1.0
            confidence = min(1.0, 0.6 + (count - MIN_CO_APPEARANCES) * 0.05)
            edges.append(ClusterEdge(
                wallet_a=addr_a,
                wallet_b=addr_b,
                heuristic="co_spend",
                confidence=round(confidence, 3),
                evidence=f"co-appeared in {count} transactions: {pair_tx_hashes[pair][:3]}",
            ))

    return edges
