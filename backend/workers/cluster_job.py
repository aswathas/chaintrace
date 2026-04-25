"""RQ job: cluster wallets around a seed address.

Demo build: returns a synthetic cluster so the UI round-trip works without
the data layer. Wire to backend.core.clustering.* once heuristics are
fully implemented.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from typing import Any, Dict

from redis import Redis
from rq import get_current_job


def run_cluster(address: str, chain: str) -> Dict[str, Any]:
    """Synchronous RQ entry point. Returns and caches a cluster result."""
    job = get_current_job()
    job_id = job.id if job else "unknown"
    rng = random.Random(address.lower())

    cluster = {
        "id": job_id,
        "seed": address,
        "chain": chain,
        "members": [
            {
                "address": "0x" + format(rng.getrandbits(160), "040x"),
                "confidence": round(rng.uniform(0.6, 0.95), 2),
                "heuristic": rng.choice(["common_funder", "fingerprint", "co_spend", "nonce_linked"]),
            }
            for _ in range(rng.randint(3, 8))
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "demo": True,
    }
    redis = Redis.from_url("redis://localhost:6379")
    redis.set(f"cluster:{job_id}", json.dumps(cluster), ex=3600)
    return cluster
