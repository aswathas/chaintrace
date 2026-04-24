"""Cross-chain bridge deposit → withdrawal matching."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

BRIDGE_TIMESTAMP_WINDOW_SECONDS = 30 * 60  # ±30 minutes
VALUE_TOLERANCE_BPS = 50  # 0.5% — accounts for bridge fees


@dataclass
class BridgeEdge:
    """Minimal representation of a bridge deposit edge — provided by the tracer engine."""
    src: str
    dst: str          # bridge contract address
    chain: str        # source chain
    tx_hash: str
    timestamp: int    # unix seconds
    value_usd: float
    token: str        # "ETH", "USDC", etc.
    dst_chain: Optional[str] = None  # if known from event logs


def _chains_to_search(deposit: BridgeEdge) -> list[str]:
    """Return candidate destination chains given the deposit's bridge label."""
    if deposit.dst_chain:
        return [deposit.dst_chain]
    # Default search order — prioritise high-volume bridge destinations
    return ["arbitrum", "optimism", "base", "polygon", "bsc", "ethereum"]


async def match_bridge_out(deposit: BridgeEdge) -> Optional[str]:
    """Given a bridge deposit edge, find the recipient address on the destination chain.

    Queries the destination chain for a mint/withdrawal event matching
    value + timestamp within ±30 min. Returns the destination address or None.
    """
    low_ts = deposit.timestamp - BRIDGE_TIMESTAMP_WINDOW_SECONDS
    high_ts = deposit.timestamp + BRIDGE_TIMESTAMP_WINDOW_SECONDS

    low_value = deposit.value_usd * (1 - VALUE_TOLERANCE_BPS / 10_000)
    high_value = deposit.value_usd * (1 + VALUE_TOLERANCE_BPS / 10_000)

    for chain in _chains_to_search(deposit):
        # TODO: wire to backend.data.providers.fallback.FallbackChain when available
        # candidate = await FallbackChain(chain).find_bridge_mint(
        #     bridge_label=deposit.dst.lower(),
        #     token=deposit.token,
        #     min_value_usd=low_value,
        #     max_value_usd=high_value,
        #     min_ts=low_ts,
        #     max_ts=high_ts,
        # )
        candidate: Optional[dict] = None  # placeholder until provider wired

        if candidate and candidate.get("recipient"):
            return candidate["recipient"]

    return None
