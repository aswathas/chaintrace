"""Hack Tracer BFS engine — hop-by-hop fund flow traversal (spec §7.1)."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .terminals import Terminal, classify_terminal, is_cold_storage, EXPLOIT_WALLETS
from .cross_chain import BridgeEdge, match_bridge_out
from .mixer_exit import DepositTx, match_tornado_exits, MixerExitCandidate

MAX_WALLETS = 500
DEFAULT_MAX_HOPS = 10
DEFAULT_MIN_VALUE_USD = 100.0
DEFAULT_FANOUT = 5


# ---------------------------------------------------------------------------
# Result models (mirrors backend.models.trace — defined here for self-containment;
# other agents' backend.models.trace must export compatible types)
# ---------------------------------------------------------------------------

@dataclass
class OutflowEdge:
    src: str
    dst: str
    tx_hash: str
    chain: str
    timestamp: int
    value_usd: float
    token: str
    block: int
    gas_price_gwei: Optional[float] = None
    dst_chain: Optional[str] = None  # set when dst is a bridge


@dataclass
class HopNode:
    address: str
    chain: str
    depth: int
    terminal: Optional[Terminal] = None
    is_exploit_wallet: bool = False
    mixer_exits: list[MixerExitCandidate] = field(default_factory=list)


@dataclass
class TraceResult:
    seed: str
    chain: str
    nodes: list[HopNode]
    edges: list[OutflowEdge]
    terminals: list[tuple[OutflowEdge, Terminal]]
    visited_count: int
    truncated: bool  # True if MAX_WALLETS hit before exhaustion
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _filter_by_value(edges: list[OutflowEdge], min_value_usd: float) -> list[OutflowEdge]:
    return [e for e in edges if e.value_usd >= min_value_usd]


def _top_n_by_value(edges: list[OutflowEdge], n: int) -> tuple[list[OutflowEdge], list[OutflowEdge]]:
    """Return (top_n, rest) sorted by value_usd descending."""
    sorted_edges = sorted(edges, key=lambda e: e.value_usd, reverse=True)
    return sorted_edges[:n], sorted_edges[n:]


async def _get_outflows(address: str, chain: str) -> list[OutflowEdge]:
    """Neo4j-first, then fall back to providers."""
    # TODO: wire to backend.data.graph.queries.get_outflows when available
    # graph_edges = await graph_client.get_outflows(address, chain)
    # if graph_edges:
    #     return graph_edges
    # TODO: wire to backend.data.providers.fallback.FallbackChain when available
    # raw = await FallbackChain(chain).fetch_txs(address)
    # edges = [_tx_to_edge(tx) for tx in raw]
    # await graph_client.upsert_edges(edges)
    # return edges
    return []  # placeholder until data layer wired


async def _resolve_labels(addresses: list[str]) -> dict[str, str]:
    """Bulk label resolution — filled by labeler.merge at runtime."""
    # TODO: wire to backend.core.labeler.merge.resolve_label when available
    return {}


# ---------------------------------------------------------------------------
# Main traversal
# ---------------------------------------------------------------------------

async def trace(
    seed_address: str,
    chain: str,
    max_hops: int = DEFAULT_MAX_HOPS,
    min_value_usd: float = DEFAULT_MIN_VALUE_USD,
    fanout: int = DEFAULT_FANOUT,
) -> TraceResult:
    """BFS traversal from seed_address; returns TraceResult with full hop graph."""
    frontier: deque[tuple[str, str, int, Optional[OutflowEdge]]] = deque()
    frontier.append((seed_address, chain, 0, None))

    visited: set[str] = set()
    nodes: list[HopNode] = []
    edges: list[OutflowEdge] = []
    terminals: list[tuple[OutflowEdge, Terminal]] = []
    additional_outflows: dict[str, list[OutflowEdge]] = {}  # for UI "show more"
    truncated = False

    while frontier:
        if len(visited) >= MAX_WALLETS:
            truncated = True
            break

        address, current_chain, depth, parent_edge = frontier.popleft()

        if address in visited or depth > max_hops:
            continue
        visited.add(address)

        is_exploit = address.lower() in EXPLOIT_WALLETS

        # Resolve labels for terminal classification
        labels = await _resolve_labels([address])

        node = HopNode(
            address=address,
            chain=current_chain,
            depth=depth,
            is_exploit_wallet=is_exploit,
        )

        # Fetch outflows
        outflows = await _get_outflows(address, current_chain)
        outflows = _filter_by_value(outflows, min_value_usd)
        top_edges, rest = _top_n_by_value(outflows, fanout)

        if rest:
            additional_outflows[address] = rest

        for edge in top_edges:
            edges.append(edge)
            dst_lower = edge.dst.lower()
            terminal = classify_terminal(dst_lower, labels)

            if terminal:
                node.terminal = terminal  # mark the node that hits the terminal
                terminals.append((edge, terminal))

                if terminal.kind == "bridge":
                    bridge_edge = BridgeEdge(
                        src=edge.src,
                        dst=edge.dst,
                        chain=edge.chain,
                        tx_hash=edge.tx_hash,
                        timestamp=edge.timestamp,
                        value_usd=edge.value_usd,
                        token=edge.token,
                        dst_chain=edge.dst_chain,
                    )
                    cross_chain_dst = await match_bridge_out(bridge_edge)
                    if cross_chain_dst:
                        dest_chain = edge.dst_chain or current_chain
                        frontier.append((cross_chain_dst, dest_chain, depth + 1, edge))

                elif terminal.kind == "mixer" and terminal.denomination is not None:
                    deposit = DepositTx(
                        tx_hash=edge.tx_hash,
                        block=edge.block,
                        timestamp=edge.timestamp,
                        denomination=terminal.denomination,
                        chain=current_chain,
                    )
                    mixer_exits = await match_tornado_exits(deposit, edge.gas_price_gwei)
                    node.mixer_exits = mixer_exits
            else:
                if dst_lower not in visited:
                    frontier.append((edge.dst, edge.dst_chain or current_chain, depth + 1, edge))

        nodes.append(node)

    return TraceResult(
        seed=seed_address,
        chain=chain,
        nodes=nodes,
        edges=edges,
        terminals=terminals,
        visited_count=len(visited),
        truncated=truncated,
        finished_at=datetime.now(timezone.utc),
    )
