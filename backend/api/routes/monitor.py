"""Real-time monitoring routes — register rules, list alerts, ingest webhooks."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from rq import Queue

from api.deps import get_redis, get_rq_queue
from data.cache.redis_cache import RedisCache
from models.alert import AlertRule

router = APIRouter(prefix="/monitor", tags=["monitor"])

_RULES_KEY = "monitor:rules"
_ALERTS_KEY = "monitor:alerts"


@router.post("", status_code=201)
async def register_rule(
    rule: AlertRule,
    redis=Depends(get_redis),
):
    """Register a wallet alert rule."""
    cache = RedisCache(redis)
    raw = await cache.get(_RULES_KEY) or []
    # Assign a new rule_id if not provided
    if not rule.rule_id:
        rule = rule.model_copy(update={"rule_id": str(uuid.uuid4())})
    raw.append(rule.model_dump(mode="json"))
    await cache.set(_RULES_KEY, raw)
    return {"rule_id": rule.rule_id}


@router.get("/alerts")
async def list_alerts(redis=Depends(get_redis)) -> List[Dict[str, Any]]:
    """Return all triggered alert events."""
    cache = RedisCache(redis)
    return await cache.get(_ALERTS_KEY) or []


@router.post("/hook")
async def ingest_webhook(
    payload: Dict[str, Any],
    queue: Queue = Depends(get_rq_queue),
    redis=Depends(get_redis),
):
    """Ingest incoming Alchemy / Moralis webhook and dispatch alert job."""
    job = queue.enqueue(
        "workers.monitor_job.process_webhook",
        kwargs={"payload": payload},
        job_timeout=60,
    )
    return {"job_id": job.id, "received": True}
