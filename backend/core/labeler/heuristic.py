"""Heuristic auto-labeling from behavior patterns — source 6 (lowest priority)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..tracer.terminals import CEX_HOT_WALLETS


@dataclass
class Label:
    address: str
    label: str
    source: str = "heuristic"
    confidence: float = 0.6


def _count_unique_recipients(outflows: list[dict]) -> int:
    return len({t.get("dst", "") for t in outflows if t.get("dst")})


def _all_equal_amounts(outflows: list[dict], tolerance: float = 0.01) -> bool:
    """True if ≥90% of outflows cluster within ±1% of a common value."""
    if len(outflows) < 10:
        return False
    from collections import Counter
    rounded = [round(t.get("value_usd", 0), 1) for t in outflows if t.get("value_usd", 0) > 0]
    if not rounded:
        return False
    most_common, count = Counter(rounded).most_common(1)[0]
    if most_common == 0:
        return False
    in_range = sum(1 for v in rounded if abs(v - most_common) / most_common <= tolerance)
    return in_range / len(rounded) >= 0.9


def _is_binance_distributor(inflows: list[dict], outflows: list[dict]) -> bool:
    """Wallet received from Binance hot wallet → then sent to multiple destinations."""
    binance_in = any(
        t.get("src", "").lower() in CEX_HOT_WALLETS
        and CEX_HOT_WALLETS.get(t.get("src", "").lower()) == "binance"
        for t in inflows
    )
    return binance_in and len(outflows) > 0


def _deploys_exploited_contract(wallet: dict, inflows: list[dict]) -> bool:
    """Wallet deployed a contract that later received large hack-labeled inflows."""
    is_deployer = wallet.get("deployed_contracts", [])
    if not is_deployer:
        return False
    # Check if any deployed contract address received exploit-tagged inflows
    deployed = {c.lower() for c in is_deployer}
    exploit_sources = any(
        t.get("label", "").lower() in ("exploit", "hack", "stolen")
        and t.get("src", "").lower() in deployed
        for t in inflows
    )
    return exploit_sources


def infer_label(
    wallet: dict[str, Any],
    behavior: dict[str, Any],
    outflows: Optional[list[dict]] = None,
    inflows: Optional[list[dict]] = None,
) -> Optional[Label]:
    """Return a single inferred label (highest confidence match), or None."""
    outflows = outflows or []
    inflows = inflows or []
    address = wallet.get("address", "")

    candidates: list[Label] = []

    # Rule 1: airdrop farmer — ≥50 unique recipients, equal amounts
    unique_recipients = _count_unique_recipients(outflows)
    if unique_recipients >= 50 and _all_equal_amounts(outflows):
        candidates.append(Label(address=address, label="airdrop_farmer", confidence=0.75))

    # Rule 2: Binance user / distributor
    if _is_binance_distributor(inflows, outflows):
        candidates.append(Label(address=address, label="binance_user", confidence=0.65))

    # Rule 3: exploited contract deployer
    if _deploys_exploited_contract(wallet, inflows):
        candidates.append(Label(address=address, label="exploited_contract_deployer", confidence=0.70))

    # Rule 4: high-volume DeFi user (≥500 txs with known protocol counterparties)
    protocol_txs = behavior.get("protocol_tx_count", 0)
    if protocol_txs >= 500:
        candidates.append(Label(address=address, label="defi_power_user", confidence=0.60))

    if not candidates:
        return None
    return max(candidates, key=lambda l: l.confidence)
