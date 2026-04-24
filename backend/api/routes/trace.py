"""Hack Tracer routes — POST /trace, GET /trace/{job_id}, WS /trace/{job_id}/stream."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from rq import Queue
from rq.job import Job

from api.deps import get_redis, get_rq_queue
from data.cache.keys import trace_key
from data.cache.redis_cache import RedisCache
from models.trace import TraceRequest

router = APIRouter(prefix="/trace", tags=["trace"])


@router.post("", status_code=202)
async def start_trace(
    request: TraceRequest,
    queue: Queue = Depends(get_rq_queue),
):
    """Enqueue a hack-trace job and return the job_id."""
    job = queue.enqueue(
        "workers.trace_job.run_trace",
        kwargs={"request": request.model_dump()},
        job_timeout=600,
    )
    return {"job_id": job.id, "status": "queued"}


@router.get("/{job_id}")
async def get_trace(
    job_id: str,
    redis=Depends(get_redis),
    queue: Queue = Depends(get_rq_queue),
):
    """Return trace result if complete, or job status if still running."""
    cache = RedisCache(redis)
    cached = await cache.get(trace_key(job_id))
    if cached:
        return cached

    try:
        job = Job.fetch(job_id, connection=queue.connection)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"job_id": job_id, "status": job.get_status()}


@router.websocket("/{job_id}/stream")
async def stream_trace(job_id: str, websocket: WebSocket, redis=Depends(get_redis)):
    """WebSocket that streams live hop updates for a running trace job."""
    await websocket.accept()
    pubsub = redis.pubsub()
    channel = f"trace:stream:{job_id}"
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"].decode())
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
