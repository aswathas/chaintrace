"""RQ job: run hack trace and stream updates."""
import asyncio
import json
from redis import Redis
from backend.core.tracer.engine import trace  # assumed to exist
from backend.data.graph.upsert import upsert_trace  # assumed to exist


def run_trace(job_id: str, seed: str, chain: str, opts: dict) -> dict:
    """Synchronous RQ job to run trace. Calls async engine via asyncio.run()."""
    redis = Redis.from_url("redis://localhost:6379")

    # Run async trace engine
    result = asyncio.run(trace(seed=seed, chain=chain, **opts))

    # Upsert into Neo4j
    asyncio.run(upsert_trace(result, chain))

    # Store result in Redis
    redis.set(f"trace:{job_id}", json.dumps(result), ex=3600)

    # Publish hop updates to pub/sub (could stream mid-execution too)
    redis.publish(f"trace:{job_id}:stream", json.dumps({"status": "complete", "hops": len(result.get("hops", []))}))

    return result
