"""Wallet Profiler routes — POST /profile, GET /profile/{address}."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from rq import Queue
from rq.job import Job

from api.deps import get_redis, get_rq_queue
from data.cache.keys import profile_key
from data.cache.redis_cache import RedisCache
from models.wallet import Address

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", status_code=202)
async def start_profile(
    request: Address,
    queue: Queue = Depends(get_rq_queue),
):
    """Enqueue a wallet-profile job and return the job_id."""
    job = queue.enqueue(
        "workers.profile_job.run_profile",
        kwargs={"address": request.address, "chain": request.chain.value},
        job_timeout=300,
    )
    return {"job_id": job.id, "status": "queued"}


@router.get("/{address}")
async def get_profile(
    address: str,
    chain: str = "eth",
    redis=Depends(get_redis),
):
    """Return cached profile for address, or 404 if not yet profiled."""
    cache = RedisCache(redis)
    cached = await cache.get(profile_key(chain, address))
    if cached is None:
        raise HTTPException(status_code=404, detail="Profile not found — submit via POST /profile")
    return cached
