"""RQ job: profile a wallet and cache result.

Demo build: returns a deterministic synthetic profile so the UI round-trip
works without API keys. Wire to backend.core.profiler.* once the data layer
is fully implemented.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from typing import Any, Dict

from redis import Redis
from rq import get_current_job


def run_profile(address: str, chain: str) -> Dict[str, Any]:
    """Synchronous RQ entry point. Returns and caches a profile result."""
    job = get_current_job()
    job_id = job.id if job else "unknown"
    rng = random.Random(address.lower())
    score = rng.randint(5, 95)
    tier = (
        "low" if score < 25 else
        "medium" if score < 50 else
        "high" if score < 75 else
        "critical"
    )

    profile = {
        "address": address,
        "chain": chain,
        "risk": {
            "score": score,
            "level": tier,
            "signals": [
                {"name": "high_velocity", "weight": 15, "category": "negative"},
                {"name": "round_amount_transfers", "weight": 10, "category": "negative"},
                {"name": "verified_protocol_use", "weight": -10, "category": "positive"},
            ],
        },
        "labels": [
            {"name": "demo: synthetic profile", "source": "heuristic", "confidence": 0.5},
        ],
        "counterparties": [
            {
                "address": "0x" + format(rng.getrandbits(160), "040x"),
                "label": "Uniswap V3 Router",
                "interaction_count": rng.randint(1, 50),
                "total_value_usd": rng.uniform(100, 50_000),
                "last_interaction": int(datetime.now(timezone.utc).timestamp()) - rng.randint(0, 30 * 86400),
            }
            for _ in range(5)
        ],
        "behavior_tags": [
            {"tag": "active_trader", "score": 0.7, "description": "Frequent on-chain swaps"},
            {"tag": "defi_user", "score": 0.6, "description": "Interacts with DEX routers"},
        ],
        "first_seen": int(datetime.now(timezone.utc).timestamp()) - rng.randint(30, 365) * 86400,
        "last_seen": int(datetime.now(timezone.utc).timestamp()) - rng.randint(0, 7) * 86400,
        "tx_count": rng.randint(10, 5000),
        "balance_usd": rng.uniform(0, 250_000),
        "job_id": job_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    redis = Redis.from_url("redis://localhost:6379")
    redis.set(f"profile:{chain}:{address.lower()}", json.dumps(profile), ex=3600)
    return profile
