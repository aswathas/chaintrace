"""Public RPC fallback provider — reads from chainlist.org-style public nodes."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List

import httpx
import structlog

from .base import ProviderError, RateLimitError
from models.transaction import TokenTransfer, Transaction
from models.wallet import Chain

log = structlog.get_logger()

# Public RPC URLs — no auth required (best-effort, may be rate-limited)
_RPC_URLS: dict[Chain, str] = {
    Chain.eth: "https://cloudflare-eth.com",
    Chain.polygon: "https://polygon-rpc.com",
    Chain.arb: "https://arb1.arbitrum.io/rpc",
    Chain.base: "https://mainnet.base.org",
    Chain.bsc: "https://bsc-dataseed.binance.org",
}

_ID = 1


class RPCProvider:
    """Minimal JSON-RPC provider using public endpoints.

    Capabilities are limited — no full tx-history. fetch_txs returns empty;
    fetch_balance uses eth_getBalance which all public RPCs support.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=20)

    def _url(self, chain: Chain) -> str:
        url = _RPC_URLS.get(chain)
        if not url:
            raise ProviderError(f"No public RPC for chain {chain}")
        return url

    async def _rpc(self, chain: Chain, method: str, params: list) -> Any:
        payload = {"jsonrpc": "2.0", "id": _ID, "method": method, "params": params}
        resp = await self._client.post(self._url(chain), json=payload)
        if resp.status_code == 429:
            raise RateLimitError("PublicRPC 429")
        if resp.status_code >= 400:
            raise ProviderError(f"PublicRPC HTTP {resp.status_code}")
        body = resp.json()
        if "error" in body:
            raise ProviderError(str(body["error"]))
        return body.get("result")

    async def fetch_txs(self, address: str, chain: Chain, limit: int = 100) -> List[Transaction]:
        # Public RPCs don't expose tx history — return empty so fallback escalates
        return []

    async def fetch_balance(self, address: str, chain: Chain) -> float:
        result = await self._rpc(chain, "eth_getBalance", [address, "latest"])
        if isinstance(result, str):
            return int(result, 16) / 1e18
        return 0.0

    async def fetch_token_transfers(
        self, address: str, chain: Chain, limit: int = 100
    ) -> List[TokenTransfer]:
        return []
