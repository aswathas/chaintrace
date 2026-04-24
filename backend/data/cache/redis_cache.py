"""Async Redis cache wrapper with TTL policy."""
from __future__ import annotations

import json
from enum import Enum
from typing import Any, Optional

import redis.asyncio as aioredis


class KeyType(str, Enum):
    tx = "tx"
    wallet_txs = "wallet_txs"
    balance = "balance"
    label = "label"
    profile = "profile"
    trace = "trace"


_PERMANENT = 0  # 0 = no expiry in our convention (set with persist)
_RECENT_TX_TTL = 300        # 5 minutes
_BALANCE_TTL = 30           # 30 seconds
_LABEL_TTL = 3600           # 1 hour
_PROFILE_TTL = 600          # 10 minutes


def ttl_for(key_type: KeyType, block_age_blocks: int = 0) -> Optional[int]:
    """Return TTL in seconds. None means store with no expiry (permanent)."""
    if key_type == KeyType.balance:
        return _BALANCE_TTL
    if key_type == KeyType.label:
        return _LABEL_TTL
    if key_type in (KeyType.tx, KeyType.wallet_txs):
        if block_age_blocks >= 1000:
            return None  # permanent — immutable old block
        return _RECENT_TX_TTL
    if key_type == KeyType.profile:
        return _PROFILE_TTL
    return _RECENT_TX_TTL


class RedisCache:
    """Thin async wrapper around redis-py with JSON serialization."""

    def __init__(self, client: aioredis.Redis) -> None:  # type: ignore[type-arg]
        self._r = client

    async def get(self, key: str) -> Optional[Any]:
        raw = await self._r.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        serialized = json.dumps(value, default=str)
        if ttl is None:
            await self._r.set(key, serialized)
        else:
            await self._r.setex(key, ttl, serialized)

    async def delete(self, key: str) -> None:
        await self._r.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._r.exists(key))

    async def ping(self) -> bool:
        try:
            return await self._r.ping()
        except Exception:  # noqa: BLE001
            return False
