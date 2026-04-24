"""Rule-based wallet risk scorer (spec §7.2)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .behavior import is_high_velocity, has_round_amounts, wallet_age_days

RiskLevel = Literal["low", "medium", "high", "critical"]

# Signal weights (spec table)
_WEIGHTS: dict[str, int] = {
    "mixer_interaction": +40,
    "darknet_counterparty": +35,
    "exploit_wallet_interaction": +30,
    "high_velocity": +15,
    "round_amounts": +10,
    "young_wallet": +5,
    "verified_protocol": -10,
    "cex_counterparty": -5,
}


def _risk_level(score: int) -> RiskLevel:
    if score < 25:
        return "low"
    if score < 50:
        return "medium"
    if score < 75:
        return "high"
    return "critical"


@dataclass
class RiskSignal:
    name: str
    weight: int
    triggered: bool
    evidence: str = ""


@dataclass
class RiskScore:
    score: int               # 0–100
    level: RiskLevel
    signals: list[RiskSignal] = field(default_factory=list)


def score(
    wallet: dict[str, Any],
    counterparties: list[dict[str, Any]],
    labels: dict[str, str],
    behavior: dict[str, Any],
) -> RiskScore:
    """Compute a 0–100 risk score; return RiskScore with per-signal breakdown."""
    signals: list[RiskSignal] = []
    raw = 0

    # --- mixer_interaction (+40) ---
    mixer_counterparties = [
        c for c in counterparties
        if "tornado" in labels.get(c.get("address", "").lower(), "").lower()
        or "mixer" in labels.get(c.get("address", "").lower(), "").lower()
    ]
    triggered = len(mixer_counterparties) > 0
    signals.append(RiskSignal(
        name="mixer_interaction",
        weight=_WEIGHTS["mixer_interaction"],
        triggered=triggered,
        evidence=f"{len(mixer_counterparties)} mixer counterparty/ies" if triggered else "",
    ))
    if triggered:
        raw += _WEIGHTS["mixer_interaction"]

    # --- darknet_counterparty (+35) ---
    darknet = [
        c for c in counterparties
        if "darknet" in labels.get(c.get("address", "").lower(), "").lower()
        or "scam" in labels.get(c.get("address", "").lower(), "").lower()
    ]
    triggered = len(darknet) > 0
    signals.append(RiskSignal(
        name="darknet_counterparty",
        weight=_WEIGHTS["darknet_counterparty"],
        triggered=triggered,
        evidence=f"{len(darknet)} darknet-labeled counterparty/ies" if triggered else "",
    ))
    if triggered:
        raw += _WEIGHTS["darknet_counterparty"]

    # --- exploit_wallet_interaction (+30) ---
    exploit = [
        c for c in counterparties
        if "exploit" in labels.get(c.get("address", "").lower(), "").lower()
        or "hack" in labels.get(c.get("address", "").lower(), "").lower()
    ]
    triggered = len(exploit) > 0
    signals.append(RiskSignal(
        name="exploit_wallet_interaction",
        weight=_WEIGHTS["exploit_wallet_interaction"],
        triggered=triggered,
        evidence=f"{len(exploit)} exploit-labeled counterparty/ies" if triggered else "",
    ))
    if triggered:
        raw += _WEIGHTS["exploit_wallet_interaction"]

    # --- high_velocity (+15) ---
    txs: list[dict] = behavior.get("txs", [])
    vel = is_high_velocity(txs)
    signals.append(RiskSignal(
        name="high_velocity",
        weight=_WEIGHTS["high_velocity"],
        triggered=vel,
        evidence="≥20 txs in a 24h window with avg gap <10min" if vel else "",
    ))
    if vel:
        raw += _WEIGHTS["high_velocity"]

    # --- round_amounts (+10) ---
    rnd = has_round_amounts(txs)
    signals.append(RiskSignal(
        name="round_amounts",
        weight=_WEIGHTS["round_amounts"],
        triggered=rnd,
        evidence="≥30% of txs are round USD amounts" if rnd else "",
    ))
    if rnd:
        raw += _WEIGHTS["round_amounts"]

    # --- young_wallet (+5) ---
    age = wallet_age_days(wallet)
    young = age < 30
    signals.append(RiskSignal(
        name="young_wallet",
        weight=_WEIGHTS["young_wallet"],
        triggered=young,
        evidence=f"wallet age {age} days" if young else "",
    ))
    if young:
        raw += _WEIGHTS["young_wallet"]

    # --- verified_protocol (-10) ---
    verified = any(
        "uniswap" in labels.get(c.get("address", "").lower(), "").lower()
        or "aave" in labels.get(c.get("address", "").lower(), "").lower()
        or "curve" in labels.get(c.get("address", "").lower(), "").lower()
        or "compound" in labels.get(c.get("address", "").lower(), "").lower()
        for c in counterparties
    )
    signals.append(RiskSignal(
        name="verified_protocol",
        weight=_WEIGHTS["verified_protocol"],
        triggered=verified,
        evidence="interacted with verified DeFi protocol" if verified else "",
    ))
    if verified:
        raw += _WEIGHTS["verified_protocol"]

    # --- cex_counterparty (-5) ---
    cex_cp = any(
        any(ex in labels.get(c.get("address", "").lower(), "").lower()
            for ex in ("binance", "coinbase", "kraken", "bitfinex", "okx", "bybit", "cex"))
        for c in counterparties
    )
    signals.append(RiskSignal(
        name="cex_counterparty",
        weight=_WEIGHTS["cex_counterparty"],
        triggered=cex_cp,
        evidence="CEX-labeled counterparty detected" if cex_cp else "",
    ))
    if cex_cp:
        raw += _WEIGHTS["cex_counterparty"]

    clamped = max(0, min(100, raw))
    return RiskScore(score=clamped, level=_risk_level(clamped), signals=signals)
