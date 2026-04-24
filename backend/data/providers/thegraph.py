"""The Graph Protocol provider — DeFi protocol data (Uniswap, Aave, bridges)."""
from __future__ import annotations

from typing import Any, Dict, List

import httpx
import structlog

from .base import ProviderError, RateLimitError
from models.transaction import TokenTransfer, Transaction
from models.wallet import Chain

log = structlog.get_logger()

# Public subgraph endpoints (decentralized network or hosted service)
_SUBGRAPHS: dict[str, str] = {
    "uniswap_v3_eth": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
    "aave_v3_eth": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
}


class TheGraphProvider:
    """Query The Graph subgraphs for DeFi interaction data.

    Note: fetch_txs / fetch_balance return empty lists — The Graph is not a
    general transaction source. Use it via query_subgraph() for DeFi-specific
    data. fetch_* stubs satisfy the Provider protocol so it can sit in a
    FallbackChain for DeFi-context queries.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30)

    async def query_subgraph(self, subgraph_url: str, query: str, variables: Dict[str, Any] | None = None) -> dict:
        """Run a raw GraphQL query against any subgraph."""
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = await self._client.post(subgraph_url, json=payload)
        if resp.status_code == 429:
            raise RateLimitError("TheGraph 429")
        if resp.status_code >= 400:
            raise ProviderError(f"TheGraph HTTP {resp.status_code}")
        body = resp.json()
        if "errors" in body:
            raise ProviderError(str(body["errors"]))
        return body.get("data", {})

    async def fetch_txs(self, address: str, chain: Chain, limit: int = 100) -> List[Transaction]:
        # The Graph is not used for raw tx lists — return empty
        return []

    async def fetch_balance(self, address: str, chain: Chain) -> float:
        return 0.0

    async def fetch_token_transfers(
        self, address: str, chain: Chain, limit: int = 100
    ) -> List[TokenTransfer]:
        return []
