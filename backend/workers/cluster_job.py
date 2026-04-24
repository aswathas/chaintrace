"""RQ job: run entity clustering around a seed address."""
import asyncio
import json
from redis import Redis
from backend.core.clustering.engine import cluster  # assumed to exist


def run_cluster(job_id: str, seed_address: str, chain: str) -> dict:
    """Synchronous RQ job to cluster wallets around a seed."""
    redis = Redis.from_url("redis://localhost:6379")

    # Run async clustering
    cluster_result = asyncio.run(cluster(seed_address, chain))

    # Store in Redis with 1-hour TTL
    redis.set(f"cluster:{job_id}", json.dumps(cluster_result), ex=3600)

    # Publish completion
    redis.publish(f"cluster:{job_id}:complete", json.dumps({"cluster_size": len(cluster_result.get("wallets", []))}))

    return cluster_result
