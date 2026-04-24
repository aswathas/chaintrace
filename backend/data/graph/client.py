"""Neo4j async driver singleton."""
from __future__ import annotations

from typing import Optional

import structlog
from neo4j import AsyncDriver, AsyncGraphDatabase

log = structlog.get_logger()

_driver: Optional[AsyncDriver] = None


async def get_driver(uri: str, password: str, user: str = "neo4j") -> AsyncDriver:
    """Return the singleton async Neo4j driver, creating it if needed."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        log.info("neo4j_connected", uri=uri)
    return _driver


async def close_driver() -> None:
    """Close the driver on shutdown."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        log.info("neo4j_closed")
