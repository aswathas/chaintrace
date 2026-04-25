"""RQ job: run a hack trace and cache the result.

Demo build: returns a synthetic trace tree (3 hops, 1 mixer terminal, 1 CEX
terminal) so the UI graph + timeline round-trip works without provider keys.
Wire to backend.core.tracer.engine once the data layer is fully implemented.
"""
from __future__ import annotations

import json
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from redis import Redis
from rq import get_current_job


def _addr(rng: random.Random) -> str:
    return "0x" + format(rng.getrandbits(160), "040x")


def run_trace(request: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous RQ entry point. Returns and caches a trace result."""
    job = get_current_job()
    job_id = job.id if job else "unknown"
    seed = request.get("seed_address", "0x0")
    chain = request.get("chain", "eth")
    max_hops = int(request.get("max_hops", 10))

    rng = random.Random(seed.lower())
    now = int(time.time())

    # Build a synthetic 3-hop trace tree
    nodes: List[Dict[str, Any]] = [
        {"address": seed, "chain": chain, "balance_usd": 0, "depth": 0, "tx_count": 1},
    ]
    edges: List[Dict[str, Any]] = []
    terminals: List[Dict[str, Any]] = []

    hop1 = _addr(rng)
    hop2 = _addr(rng)
    mixer = "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936"  # Tornado 1 ETH (well-known)
    cex = "0x28c6c06298d514db089934071355e5743bf21d60"    # Binance hot wallet

    nodes.extend([
        {"address": hop1, "chain": chain, "balance_usd": 0, "depth": 1, "tx_count": 4},
        {"address": hop2, "chain": chain, "balance_usd": 0, "depth": 2, "tx_count": 2},
        {"address": mixer, "chain": chain, "balance_usd": 0, "depth": 3,
         "tx_count": 12_000, "label": "Tornado Cash 1 ETH", "terminal_type": "mixer"},
        {"address": cex, "chain": chain, "balance_usd": 0, "depth": 3,
         "tx_count": 3_500_000, "label": "Binance Hot Wallet", "terminal_type": "cex"},
    ])

    def _edge(src: str, dst: str, value_usd: float) -> Dict[str, Any]:
        return {
            "from": src,
            "to": dst,
            "tx_hash": "0x" + format(rng.getrandbits(256), "064x"),
            "block": now // 12,
            "timestamp": now - rng.randint(0, 86400),
            "value": str(int(value_usd * 1e18)),
            "value_usd": value_usd,
            "token": "ETH",
            "chain": chain,
        }

    edges.append(_edge(seed, hop1, 1500.0))
    edges.append(_edge(hop1, hop2, 800.0))
    edges.append(_edge(hop1, mixer, 700.0))
    edges.append(_edge(hop2, cex, 750.0))

    terminals.extend([
        {"address": mixer, "terminal_type": "mixer", "confidence": 0.92},
        {"address": cex, "terminal_type": "cex", "confidence": 0.99},
    ])

    result = {
        "id": job_id,
        "seed": seed,
        "chain": chain,
        "nodes": nodes,
        "edges": edges,
        "terminals": terminals,
        "created_at": now,
        "hops_count": min(3, max_hops),
        "demo": True,
    }

    redis = Redis.from_url("redis://localhost:6379")
    redis.set(f"trace:{job_id}", json.dumps(result), ex=3600)
    redis.publish(
        f"trace:stream:{job_id}",
        json.dumps({"type": "done", "payload": result}),
    )
    return result
