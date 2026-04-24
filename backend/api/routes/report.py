"""Report generation route — POST /report/{job_id}."""
from __future__ import annotations

import importlib
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_redis
from data.cache.keys import trace_key
from data.cache.redis_cache import RedisCache

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/{job_id}")
async def generate_report(
    job_id: str,
    kind: str = "trace",
    redis=Depends(get_redis),
) -> Dict[str, Any]:
    """Generate an AI-formatted report for a completed trace/profile job."""
    cache = RedisCache(redis)
    context = await cache.get(trace_key(job_id))
    if context is None:
        raise HTTPException(status_code=404, detail="No result found for job_id")

    # Lazy import — ai module is owned by a different agent
    try:
        ai_mod = importlib.import_module("ai")
        report_text: str = await ai_mod.generate_report(kind=kind, context=context)
    except ImportError:
        raise HTTPException(status_code=503, detail="AI module not yet available")

    return {"job_id": job_id, "kind": kind, "report": report_text}
