"""Label resolution and community submission routes."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_redis
from data.cache.keys import label_key
from data.cache.redis_cache import KeyType, RedisCache, ttl_for
from models.label import Label, LabelSource

router = APIRouter(prefix="/labels", tags=["labels"])


@router.get("/{address}")
async def get_label(address: str, redis=Depends(get_redis)) -> Dict[str, Any]:
    """Return the merged label for an address (Redis cache → 404 if unknown)."""
    cache = RedisCache(redis)
    label_data = await cache.get(label_key(address))
    if label_data is None:
        raise HTTPException(status_code=404, detail="No label found for address")
    return label_data


@router.post("", status_code=201)
async def submit_label(
    label: Label,
    redis=Depends(get_redis),
) -> Dict[str, Any]:
    """Accept a community label submission and cache it pending review."""
    cache = RedisCache(redis)

    # Assign missing fields
    enriched = label.model_copy(
        update={
            "source": LabelSource.submission,
            "created_at": label.created_at or datetime.now(timezone.utc),
        }
    )

    existing: List[dict] = await cache.get(label_key(label.address)) or []
    if not isinstance(existing, list):
        existing = [existing]

    existing.append(enriched.model_dump(mode="json"))
    await cache.set(label_key(label.address), existing, ttl=ttl_for(KeyType.label))
    return {"address": label.address, "status": "submitted"}
