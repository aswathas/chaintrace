"""RQ job: run wallet profiler and cache result."""
import asyncio
import json
from redis import Redis
from backend.core.profiler.scorer import score  # assumed to exist
from backend.core.profiler.summary import summarize  # assumed to exist


def run_profile(job_id: str, address: str, chain: str) -> dict:
    """Synchronous RQ job to profile a wallet."""
    redis = Redis.from_url("redis://localhost:6379")

    # Run async profiler
    profile = asyncio.run(_profile_async(address, chain))

    # Store in Redis with 1-hour TTL
    redis.set(f"profile:{address}:{chain}", json.dumps(profile), ex=3600)

    # Publish completion
    redis.publish(f"profile:{job_id}:complete", json.dumps(profile))

    return profile


async def _profile_async(address: str, chain: str) -> dict:
    """Async profiler logic."""
    risk_score = await score(address, chain)
    summary = await summarize(address, chain, risk_score)
    return {
        "address": address,
        "chain": chain,
        "risk_score": risk_score,
        **summary,
    }
