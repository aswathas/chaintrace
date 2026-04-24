"""Stateless behavioral helper functions for the profiler."""
from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any


def is_high_velocity(txs: list[dict[str, Any]]) -> bool:
    """True if avg inter-tx gap < 10 minutes and tx count > 20 in any 24h window."""
    if len(txs) < 20:
        return False
    # Sort by timestamp ascending
    sorted_ts = sorted(t["timestamp"] for t in txs if "timestamp" in t)
    if len(sorted_ts) < 2:
        return False

    # Sliding 24h window count
    window = 86400  # seconds
    max_in_window = 0
    left = 0
    for right in range(len(sorted_ts)):
        while sorted_ts[right] - sorted_ts[left] > window:
            left += 1
        max_in_window = max(max_in_window, right - left + 1)

    if max_in_window < 20:
        return False

    # Check average inter-tx gap
    gaps = [sorted_ts[i + 1] - sorted_ts[i] for i in range(len(sorted_ts) - 1)]
    avg_gap_minutes = statistics.mean(gaps) / 60
    return avg_gap_minutes < 10


def has_round_amounts(txs: list[dict[str, Any]], threshold: float = 0.30) -> bool:
    """True if >= threshold fraction of txs have a round USD value (multiple of 10)."""
    if not txs:
        return False
    values = [t.get("value_usd", 0) for t in txs if t.get("value_usd", 0) > 0]
    if not values:
        return False
    round_count = sum(1 for v in values if v >= 10 and round(v, 0) % 10 == 0 and abs(v - round(v, 0)) < 0.01)
    return (round_count / len(values)) >= threshold


def wallet_age_days(wallet: dict[str, Any]) -> int:
    """Days since wallet first appeared on-chain."""
    first_seen = wallet.get("first_seen")
    if first_seen is None:
        return 9999
    if isinstance(first_seen, (int, float)):
        first_dt = datetime.fromtimestamp(first_seen, tz=timezone.utc)
    elif isinstance(first_seen, datetime):
        first_dt = first_seen if first_seen.tzinfo else first_seen.replace(tzinfo=timezone.utc)
    else:
        return 9999
    return (datetime.now(timezone.utc) - first_dt).days


def gas_price_fingerprint(txs: list[dict[str, Any]], bins: int = 20) -> list[float]:
    """Histogram of gas prices normalised to [0, 1] — used for fingerprint clustering."""
    prices = [t.get("gas_price_gwei", 0) for t in txs if t.get("gas_price_gwei", 0) > 0]
    if not prices:
        return [0.0] * bins
    min_p, max_p = min(prices), max(prices)
    if min_p == max_p:
        result = [0.0] * bins
        result[0] = 1.0
        return result
    histogram = [0] * bins
    for p in prices:
        bucket = int((p - min_p) / (max_p - min_p) * (bins - 1))
        histogram[bucket] += 1
    total = sum(histogram)
    return [h / total for h in histogram]
