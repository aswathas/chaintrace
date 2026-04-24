"""Priority-ordered label merge — calls all 6 sources and returns winner + provenance."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .hardcoded import HARDCODED_LABELS
from .community import Label, load_community_labels
from .etherscan import scrape_etherscan_tag
from .arkham import fetch_arkham_label
from .submissions import get_user_labels
from .heuristic import infer_label


@dataclass
class LabelBundle:
    address: str
    winner: Optional[Label]          # highest-priority non-null label
    provenance: list[Label]          # all non-null results across sources
    source_order: list[str] = field(default_factory=list)


async def resolve_label(
    address: str,
    chain: str = "ethereum",
    wallet: Optional[dict[str, Any]] = None,
    behavior: Optional[dict[str, Any]] = None,
    outflows: Optional[list[dict]] = None,
    inflows: Optional[list[dict]] = None,
) -> LabelBundle:
    """Resolve an address through all 6 label sources; return priority-ordered bundle."""
    addr_lower = address.lower()
    provenance: list[Label] = []
    winner: Optional[Label] = None

    # Source 1 — Hardcoded (highest confidence)
    hc_str = HARDCODED_LABELS.get(addr_lower)
    if hc_str:
        lbl = Label(address=addr_lower, label=hc_str, source="hardcoded", confidence=1.0)
        provenance.append(lbl)
        if winner is None:
            winner = lbl

    # Source 2 — Community repos (Postgres snapshot)
    community = await load_community_labels()
    comm_lbl = community.get(addr_lower)
    if comm_lbl:
        provenance.append(comm_lbl)
        if winner is None:
            winner = comm_lbl

    # Source 3 — Etherscan public tags
    eth_lbl = await scrape_etherscan_tag(address, chain)
    if eth_lbl:
        provenance.append(eth_lbl)
        if winner is None:
            winner = eth_lbl

    # Source 4 — Arkham Intelligence
    arkham_lbl = await fetch_arkham_label(address)
    if arkham_lbl:
        provenance.append(arkham_lbl)
        if winner is None:
            winner = arkham_lbl

    # Source 5 — User submissions
    user_lbls = await get_user_labels(address)
    for u in user_lbls:
        provenance.append(u)
    if user_lbls and winner is None:
        winner = user_lbls[0]  # newest first

    # Source 6 — Heuristic (lowest priority)
    if wallet is not None:
        h_lbl = infer_label(wallet, behavior or {}, outflows, inflows)
        if h_lbl:
            provenance.append(h_lbl)
            if winner is None:
                winner = h_lbl

    return LabelBundle(
        address=addr_lower,
        winner=winner,
        provenance=provenance,
        source_order=["hardcoded", "community", "etherscan", "arkham", "submissions", "heuristic"],
    )
