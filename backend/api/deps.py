"""FastAPI shared dependencies."""
from __future__ import annotations

from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends
from neo4j import AsyncDriver
from rq import Queue

from config import get_settings
from data.graph.client import get_driver as _get_driver

_settings = get_settings()

# Module-level singletons set during app startup
_redis_client: aioredis.Redis | None = None  # type: ignore[type-arg]
_neo4j_driver: AsyncDriver | None = None
_rq_queue: Queue | None = None


def set_redis(client: aioredis.Redis) -> None:  # type: ignore[type-arg]
    global _redis_client
    _redis_client = client


def set_neo4j(driver: AsyncDriver) -> None:
    global _neo4j_driver
    _neo4j_driver = driver


def set_rq(queue: Queue) -> None:
    global _rq_queue
    _rq_queue = queue


async def get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    """Yield the Redis async client."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialised")
    return _redis_client


async def get_neo4j() -> AsyncDriver:
    """Yield the Neo4j async driver."""
    if _neo4j_driver is None:
        raise RuntimeError("Neo4j driver not initialised")
    return _neo4j_driver


async def get_rq_queue() -> Queue:
    """Yield the RQ queue."""
    if _rq_queue is None:
        raise RuntimeError("RQ queue not initialised")
    return _rq_queue


async def get_pg():
    """Placeholder — returns a SQLAlchemy async session.

    TODO(workers/core agent): Wire up AsyncSession from sqlalchemy once
    Postgres migrations are in place.
    """
    raise NotImplementedError("Postgres session not yet wired")
