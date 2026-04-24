"""Nonce-linked clustering — contract deployer + wallet that funded the deployer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ClusterEdge:
    wallet_a: str
    wallet_b: str
    heuristic: str
    confidence: float
    evidence: str = ""


def find_nonce_linked_clusters(
    deployed_contracts: list[dict[str, Any]],
    funding_edges: list[dict[str, Any]],
) -> list[ClusterEdge]:
    """Link a contract deployer to the wallet that funded the deployer.

    deployed_contracts: list of {deployer: str, contract: str, tx_hash: str}
    funding_edges: list of {src: str, dst: str, tx_hash: str, timestamp: int}

    The heuristic: deployer D created contract C; wallet F funded D before the deploy.
    F and C are likely the same entity.
    """
    # Build a lookup: who funded each deployer?
    funded_by: dict[str, list[str]] = {}
    for edge in funding_edges:
        dst = edge.get("dst", "").lower()
        src = edge.get("src", "").lower()
        if dst and src:
            funded_by.setdefault(dst, []).append(src)

    edges: list[ClusterEdge] = []
    seen: set[frozenset] = set()

    for deploy in deployed_contracts:
        deployer = deploy.get("deployer", "").lower()
        contract = deploy.get("contract", "").lower()
        if not deployer or not contract:
            continue

        funders = funded_by.get(deployer, [])
        for funder in funders:
            pair = frozenset({funder, deployer})
            if pair in seen:
                continue
            seen.add(pair)
            edges.append(ClusterEdge(
                wallet_a=funder,
                wallet_b=deployer,
                heuristic="nonce_linked",
                confidence=0.75,
                evidence=f"{funder} funded deployer {deployer} which deployed {contract}",
            ))

    return edges
