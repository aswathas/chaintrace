"""Common funder clustering — wallets first-funded by the same address within 7 days."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

WINDOW_SECONDS = 7 * 24 * 3600  # 7 days


@dataclass
class ClusterEdge:
    wallet_a: str
    wallet_b: str
    heuristic: str
    confidence: float
    evidence: str = ""


def find_common_funder_clusters(
    wallets: list[dict[str, Any]],
) -> list[ClusterEdge]:
    """Return edges for wallet pairs that share a first-funder within a 7-day window.

    Each wallet dict must have: address, first_funder, first_funded_at (unix ts).
    """
    # Group wallets by their first funder
    funder_groups: dict[str, list[dict]] = defaultdict(list)
    for w in wallets:
        funder = w.get("first_funder")
        if funder:
            funder_groups[funder.lower()].append(w)

    edges: list[ClusterEdge] = []

    for funder, group in funder_groups.items():
        # Sort by first_funded_at to enable sliding window
        group_sorted = sorted(group, key=lambda w: w.get("first_funded_at", 0))
        n = len(group_sorted)
        for i in range(n):
            for j in range(i + 1, n):
                ts_i = group_sorted[i].get("first_funded_at", 0)
                ts_j = group_sorted[j].get("first_funded_at", 0)
                if abs(ts_j - ts_i) <= WINDOW_SECONDS:
                    addr_a = group_sorted[i]["address"].lower()
                    addr_b = group_sorted[j]["address"].lower()
                    # Confidence higher when funded very close together
                    delta_hours = abs(ts_j - ts_i) / 3600
                    confidence = max(0.6, 1.0 - (delta_hours / (7 * 24)))
                    edges.append(ClusterEdge(
                        wallet_a=addr_a,
                        wallet_b=addr_b,
                        heuristic="common_funder",
                        confidence=round(confidence, 3),
                        evidence=f"both first-funded by {funder} within {delta_hours:.1f}h",
                    ))
                else:
                    # Groups are sorted — no need to continue
                    break

    return edges
