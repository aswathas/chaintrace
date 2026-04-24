"""Tornado Cash mixer exit candidate matching (spec §7.3)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

WITHDRAWAL_WINDOW_SECONDS = 72 * 3600  # 72-hour scan window

# Scoring weights — sum to 1.0
W_TIMING = 0.40
W_GAS = 0.35
W_BEHAVIOR = 0.25


@dataclass
class DepositTx:
    tx_hash: str
    block: int
    timestamp: int     # unix seconds
    denomination: float  # 0.1 / 1 / 10 / 100 ETH
    chain: str = "ethereum"


@dataclass
class WithdrawalEvent:
    tx_hash: str
    block: int
    timestamp: int
    denomination: float
    recipient: str
    gas_price_gwei: float
    relayer: Optional[str] = None


@dataclass
class MixerExitCandidate:
    recipient: str
    tx_hash: str
    timestamp: int
    denomination: float
    confidence: float
    unconfirmed: bool = True
    timing_score: float = 0.0
    gas_score: float = 0.0
    behavior_score: float = 0.0


def _timing_score(deposit_ts: int, withdrawal_ts: int) -> float:
    """Closer withdrawals score higher; exponential decay over 72h window."""
    delta_hours = abs(withdrawal_ts - deposit_ts) / 3600
    if delta_hours > 72:
        return 0.0
    # Gaussian-shaped: peak at 0h, decays to ~0.05 at 72h
    return math.exp(-((delta_hours / 20) ** 2))


def _gas_score(deposit_gas: Optional[float], withdrawal_gas: float) -> float:
    """Wallets often reuse the same gas price; penalise large divergence."""
    if deposit_gas is None or deposit_gas <= 0:
        return 0.5  # neutral when deposit gas unknown
    ratio = min(deposit_gas, withdrawal_gas) / max(deposit_gas, withdrawal_gas)
    return ratio  # 1.0 = identical, 0.0 = very different


def _behavior_score(recipient_behavior: Optional[dict]) -> float:
    """Score based on recipient wallet behavior patterns post-withdrawal."""
    if not recipient_behavior:
        return 0.5  # neutral
    score = 0.5
    # Immediate dispersion → more likely a launderer
    if recipient_behavior.get("immediate_dispersion"):
        score += 0.3
    # Known CEX deposits shortly after → moderately suspicious
    if recipient_behavior.get("cex_deposit_within_24h"):
        score += 0.15
    # Fresh wallet (no history) → more suspicious
    if recipient_behavior.get("wallet_age_days", 999) < 7:
        score += 0.15
    return min(score, 1.0)


async def match_tornado_exits(
    deposit_tx: DepositTx,
    deposit_gas_gwei: Optional[float] = None,
) -> list[MixerExitCandidate]:
    """Scan Tornado Cash withdrawals of the same denomination in a 72h window.

    Returns a list of MixerExitCandidate ordered by descending confidence.
    Each candidate carries unconfirmed=True — never present as confirmed.
    """
    window_end = deposit_tx.timestamp + WITHDRAWAL_WINDOW_SECONDS

    # TODO: wire to backend.data.providers.fallback.FallbackChain when available
    # raw_withdrawals: list[WithdrawalEvent] = await FallbackChain(deposit_tx.chain).get_tornado_withdrawals(
    #     denomination=deposit_tx.denomination,
    #     from_ts=deposit_tx.timestamp,
    #     to_ts=window_end,
    # )
    raw_withdrawals: list[WithdrawalEvent] = []  # placeholder until provider wired

    candidates: list[MixerExitCandidate] = []

    for w in raw_withdrawals:
        if w.denomination != deposit_tx.denomination:
            continue
        if not (deposit_tx.timestamp <= w.timestamp <= window_end):
            continue

        t_score = _timing_score(deposit_tx.timestamp, w.timestamp)
        g_score = _gas_score(deposit_gas_gwei, w.gas_price_gwei)

        # TODO: fetch recipient behavior from backend.data.graph when available
        # behavior = await graph.get_behavior_summary(w.recipient, deposit_tx.chain)
        behavior: Optional[dict] = None
        b_score = _behavior_score(behavior)

        confidence = W_TIMING * t_score + W_GAS * g_score + W_BEHAVIOR * b_score

        candidates.append(MixerExitCandidate(
            recipient=w.recipient,
            tx_hash=w.tx_hash,
            timestamp=w.timestamp,
            denomination=w.denomination,
            confidence=round(confidence, 4),
            unconfirmed=True,
            timing_score=round(t_score, 4),
            gas_score=round(g_score, 4),
            behavior_score=round(b_score, 4),
        ))

    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return candidates
