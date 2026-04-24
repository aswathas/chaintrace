"""Arkham Intelligence free API label fetcher — source 4 of the label pipeline."""
from __future__ import annotations

import os
from typing import Optional

from .community import Label

ARKHAM_API_BASE = "https://api.arkhamintelligence.com"
ARKHAM_ENTITY_ENDPOINT = f"{ARKHAM_API_BASE}/intelligence/address/{{address}}"


async def fetch_arkham_label(address: str) -> Optional[Label]:
    """Call Arkham free API for entity label; cache result 1 hour."""
    api_key = os.environ.get("ARKHAM_API_KEY", "")
    cache_key = f"arkham_label:{address.lower()}"

    # TODO: wire to backend.data.cache.redis_cache when available
    # cached = await redis_cache.get(cache_key)
    # if cached:
    #     return Label(**cached) if cached != "null" else None
    cached = None

    if not api_key:
        return None

    url = ARKHAM_ENTITY_ENDPOINT.format(address=address)
    headers = {"API-Key": api_key}

    # TODO: wire to httpx when available
    # async with httpx.AsyncClient(timeout=10) as client:
    #     try:
    #         resp = await client.get(url, headers=headers)
    #         if resp.status_code == 404:
    #             # TODO: cache null: await redis_cache.set(cache_key, "null", ttl=3600)
    #             return None
    #         resp.raise_for_status()
    #         data = resp.json()
    #     except Exception:
    #         return None
    data: Optional[dict] = None  # placeholder until httpx wired

    if data is None:
        return None

    # Arkham response shape: {"arkhamEntity": {"name": "...", "type": "..."}}
    entity = data.get("arkhamEntity") or {}
    name = entity.get("name") or entity.get("type")
    if not name:
        # TODO: cache null
        return None

    label = Label(
        address=address.lower(),
        label=name,
        source="arkham",
        confidence=0.80,
    )
    # TODO: cache: await redis_cache.set(cache_key, label.__dict__, ttl=3600)
    return label
