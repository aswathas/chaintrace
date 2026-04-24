"""Wallet profile aggregation — counterparties, frequency, behavior tags."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from .behavior import is_high_velocity, has_round_amounts, wallet_age_days, gas_price_fingerprint
from ..tracer.terminals import CEX_HOT_WALLETS, TORNADO_POOLS

TOP_COUNTERPARTY_COUNT = 10


@dataclass
class CounterpartyEntry:
    address: str
    label: Optional[str]
    total_value_usd: float
    tx_count: int
    direction: str  # "in" | "out" | "both"


@dataclass
class ProfileResult:
    address: str
    chain: str
    wallet_age_days: int
    tx_count: int
    total_inflow_usd: float
    total_outflow_usd: float
    top_counterparties: list[CounterpartyEntry]
    behavior_tags: list[str]
    mixer_interactions: int
    has_high_velocity: bool
    has_round_amounts: bool
    gas_fingerprint: list[float]
    unique_tokens: list[str]
    notes: list[str] = field(default_factory=list)


def _infer_behavior_tags(
    wallet: dict[str, Any],
    outflows: list[dict[str, Any]],
    inflows: list[dict[str, Any]],
    labels: dict[str, str],
) -> list[str]:
    tags: list[str] = []
    all_txs = outflows + inflows

    # Airdrop farmer: ≥50 distinct equal-amount outbound txs
    if len(outflows) >= 50:
        out_amounts = [round(o.get("value_usd", 0), 2) for o in outflows]
        most_common_val, count = Counter(out_amounts).most_common(1)[0] if out_amounts else (0, 0)
        if count >= 50 and most_common_val > 0:
            tags.append("airdrop_farmer")

    # MEV bot: high velocity + very low tx value variation + self-funded
    if is_high_velocity(all_txs) and len(outflows) > 100:
        values = [o.get("value_usd", 0) for o in outflows]
        if values and max(values) > 0:
            cv = (sum((v - sum(values) / len(values)) ** 2 for v in values) / len(values)) ** 0.5 / (sum(values) / len(values))
            if cv < 0.1:
                tags.append("mev_bot")

    # Binance user: receives from Binance hot wallet → distributes
    binance_inflows = [
        t for t in inflows
        if t.get("src", "").lower() in CEX_HOT_WALLETS
        and CEX_HOT_WALLETS.get(t.get("src", "").lower()) == "binance"
    ]
    if binance_inflows and len(outflows) > 0:
        tags.append("binance_user")

    # Exchange user (generic): any CEX inflow
    cex_in = any(t.get("src", "").lower() in CEX_HOT_WALLETS for t in inflows)
    cex_out = any(t.get("dst", "").lower() in CEX_HOT_WALLETS for t in outflows)
    if cex_in or cex_out:
        if "binance_user" not in tags:
            tags.append("exchange_user")

    # High velocity trader
    if is_high_velocity(all_txs) and "mev_bot" not in tags:
        tags.append("high_frequency_trader")

    # Smart contract deployer
    deploys = [t for t in outflows if t.get("is_contract_creation", False)]
    if deploys:
        tags.append("contract_deployer")

    # NFT trader (heuristic: ERC-721 transfers)
    nft_txs = [t for t in all_txs if t.get("token_standard") == "ERC721"]
    if len(nft_txs) >= 5:
        tags.append("nft_trader")

    return tags


def summarize(
    wallet: dict[str, Any],
    outflows: list[dict[str, Any]],
    inflows: list[dict[str, Any]],
    labels: dict[str, str],
) -> ProfileResult:
    """Aggregate wallet data into a ProfileResult."""
    address = wallet.get("address", "")
    chain = wallet.get("chain", "ethereum")

    # Totals
    total_in = sum(t.get("value_usd", 0) for t in inflows)
    total_out = sum(t.get("value_usd", 0) for t in outflows)

    # Mixer interactions
    mixer_count = sum(
        1 for t in outflows
        if t.get("dst", "").lower() in TORNADO_POOLS
        or "tornado" in labels.get(t.get("dst", "").lower(), "").lower()
    )

    # Top counterparties by total value
    cp_value: dict[str, float] = defaultdict(float)
    cp_txcount: dict[str, int] = defaultdict(int)
    cp_direction: dict[str, set] = defaultdict(set)

    for t in inflows:
        src = t.get("src", "")
        if src:
            cp_value[src] += t.get("value_usd", 0)
            cp_txcount[src] += 1
            cp_direction[src].add("in")

    for t in outflows:
        dst = t.get("dst", "")
        if dst:
            cp_value[dst] += t.get("value_usd", 0)
            cp_txcount[dst] += 1
            cp_direction[dst].add("out")

    top_cps = sorted(cp_value.items(), key=lambda x: x[1], reverse=True)[:TOP_COUNTERPARTY_COUNT]
    top_counterparties = [
        CounterpartyEntry(
            address=addr,
            label=labels.get(addr.lower()),
            total_value_usd=round(val, 2),
            tx_count=cp_txcount[addr],
            direction="both" if len(cp_direction[addr]) == 2 else next(iter(cp_direction[addr])),
        )
        for addr, val in top_cps
    ]

    all_txs = outflows + inflows
    unique_tokens = list({t.get("token", "") for t in all_txs if t.get("token")})
    behavior_tags = _infer_behavior_tags(wallet, outflows, inflows, labels)

    return ProfileResult(
        address=address,
        chain=chain,
        wallet_age_days=wallet_age_days(wallet),
        tx_count=len(all_txs),
        total_inflow_usd=round(total_in, 2),
        total_outflow_usd=round(total_out, 2),
        top_counterparties=top_counterparties,
        behavior_tags=behavior_tags,
        mixer_interactions=mixer_count,
        has_high_velocity=is_high_velocity(all_txs),
        has_round_amounts=has_round_amounts(all_txs),
        gas_fingerprint=gas_price_fingerprint(all_txs),
        unique_tokens=unique_tokens,
    )
