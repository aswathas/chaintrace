"""Union-find merger — combines all four clustering heuristics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .common_funder import find_common_funder_clusters
from .fingerprint import find_fingerprint_clusters
from .nonce_linked import find_nonce_linked_clusters
from .co_spend import find_co_spend_clusters

# Import ClusterEdge from one canonical location (common_funder is the reference)
from .common_funder import ClusterEdge

MIN_CONFIDENCE = 0.6


# ---------------------------------------------------------------------------
# Union-Find (path-compressed)
# ---------------------------------------------------------------------------

class _UnionFind:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}
        self._rank: dict[str, int] = {}

    def find(self, x: str) -> str:
        if x not in self._parent:
            self._parent[x] = x
            self._rank[x] = 0
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])  # path compression
        return self._parent[x]

    def union(self, x: str, y: str) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._parent[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1

    def groups(self) -> dict[str, list[str]]:
        """Return {root: [members]} for all groups of size ≥ 2."""
        from collections import defaultdict
        g: dict[str, list[str]] = defaultdict(list)
        for node in self._parent:
            g[self.find(node)].append(node)
        return {root: members for root, members in g.items() if len(members) >= 2}


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class Cluster:
    id: str
    members: list[str]
    edges: list[ClusterEdge]
    heuristics: list[str]
    min_confidence: float
    max_confidence: float


@dataclass
class ClusterResult:
    clusters: list[Cluster]
    all_edges: list[ClusterEdge]
    dropped_edges: list[ClusterEdge]  # below min_confidence


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def cluster_wallets(
    wallets: list[dict[str, Any]],
    wallet_txs: Optional[dict[str, list[dict]]] = None,
    deployed_contracts: Optional[list[dict]] = None,
    funding_edges: Optional[list[dict]] = None,
    multi_party_txs: Optional[list[dict]] = None,
    min_confidence: float = MIN_CONFIDENCE,
) -> ClusterResult:
    """Run all four heuristics; merge via union-find; return ClusterResult."""
    all_edges: list[ClusterEdge] = []

    # Heuristic 1: common funder
    all_edges.extend(find_common_funder_clusters(wallets))

    # Heuristic 2: behavioral fingerprint
    if wallet_txs:
        all_edges.extend(find_fingerprint_clusters(wallet_txs))

    # Heuristic 3: nonce-linked
    if deployed_contracts and funding_edges:
        nonce_edges = find_nonce_linked_clusters(deployed_contracts, funding_edges)
        # Adapt ClusterEdge type from nonce_linked to common_funder's shape
        for e in nonce_edges:
            all_edges.append(ClusterEdge(
                wallet_a=e.wallet_a, wallet_b=e.wallet_b,
                heuristic=e.heuristic, confidence=e.confidence, evidence=e.evidence,
            ))

    # Heuristic 4: co-spend
    if multi_party_txs:
        co_edges = find_co_spend_clusters(multi_party_txs)
        for e in co_edges:
            all_edges.append(ClusterEdge(
                wallet_a=e.wallet_a, wallet_b=e.wallet_b,
                heuristic=e.heuristic, confidence=e.confidence, evidence=e.evidence,
            ))

    # Filter by confidence
    kept: list[ClusterEdge] = [e for e in all_edges if e.confidence >= min_confidence]
    dropped: list[ClusterEdge] = [e for e in all_edges if e.confidence < min_confidence]

    # Union-find merge
    uf = _UnionFind()
    for edge in kept:
        uf.union(edge.wallet_a, edge.wallet_b)

    # Build cluster objects
    groups = uf.groups()
    edge_index: dict[str, list[ClusterEdge]] = {}
    for root, members in groups.items():
        member_set = set(members)
        group_edges = [
            e for e in kept
            if e.wallet_a in member_set or e.wallet_b in member_set
        ]
        edge_index[root] = group_edges

    clusters: list[Cluster] = []
    for root, members in groups.items():
        group_edges = edge_index.get(root, [])
        heuristics = list({e.heuristic for e in group_edges})
        confidences = [e.confidence for e in group_edges]
        clusters.append(Cluster(
            id=root,
            members=sorted(members),
            edges=group_edges,
            heuristics=heuristics,
            min_confidence=min(confidences) if confidences else 0.0,
            max_confidence=max(confidences) if confidences else 0.0,
        ))

    return ClusterResult(clusters=clusters, all_edges=kept, dropped_edges=dropped)
