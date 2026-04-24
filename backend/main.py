"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict

import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rq import Queue

from api import deps
from api.middleware import RequestLoggingMiddleware
from api.routes import router
from config import get_settings
from data.graph.client import close_driver, get_driver

log = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and tear down Neo4j + Redis connections."""
    # Startup
    redis_client = await aioredis.from_url(settings.redis_url, decode_responses=False)
    deps.set_redis(redis_client)
    log.info("redis_connected", url=settings.redis_url)

    neo4j_driver = await get_driver(settings.neo4j_uri, settings.neo4j_password)
    deps.set_neo4j(neo4j_driver)

    # RQ queue uses a sync Redis connection (RQ does not support asyncio)
    import redis as sync_redis
    sync_conn = sync_redis.from_url(settings.redis_url)
    q = Queue(connection=sync_conn)
    deps.set_rq(q)
    log.info("rq_queue_ready")

    yield

    # Shutdown
    await close_driver()
    await redis_client.aclose()
    log.info("shutdown_complete")


app = FastAPI(
    title="ChainTrace",
    description="Open-source multi-chain blockchain forensics API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health() -> Dict[str, Any]:
    """Report connectivity status for Neo4j, Redis, and provider key pools."""
    from data.cache.redis_cache import RedisCache

    redis_ok = False
    try:
        cache = RedisCache(deps._redis_client)  # type: ignore[arg-type]
        redis_ok = await cache.ping()
    except Exception:
        pass

    neo4j_ok = False
    try:
        driver = deps._neo4j_driver
        if driver:
            async with driver.session() as session:
                await session.run("RETURN 1")
            neo4j_ok = True
    except Exception:
        pass

    from config import get_settings as _gs
    s = _gs()
    etherscan_keys_total = len(s.etherscan_keys)

    return {
        "status": "ok" if (redis_ok and neo4j_ok) else "degraded",
        "redis": redis_ok,
        "neo4j": neo4j_ok,
        "provider_pool": {
            "etherscan_keys": etherscan_keys_total,
            "covalent": bool(s.covalent_api_key),
            "alchemy": bool(s.alchemy_api_key),
        },
    }
