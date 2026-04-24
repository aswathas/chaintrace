"""Alchemy API provider — ETH, Polygon, Arbitrum, Base, Solana."""
from __future__ import annotations

from datetime import datetime
from typing import List

import httpx
import structlog

from .base import ProviderError, RateLimitError
from models.transaction import TokenTransfer, Transaction
from models.wallet import Chain

log = structlog.get_logger()

_CHAIN_NETWORK: dict[Chain, str] = {
    Chain.eth: "eth-mainnet",
    Chain.polygon: "polygon-mainnet",
    Chain.arb: "arb-mainnet",
    Chain.base: "base-mainnet",
    Chain.bsc: "bnb-mainnet",  # limited support
    Chain.solana: "solana-mainnet",
}


class AlchemyProvider:
    """Implements Provider using the Alchemy v2/v3 API."""

    def __init__(self, api_key: str) -> None:
        self._key = api_key
        self._client = httpx.AsyncClient(timeout=30)

    def _url(self, chain: Chain) -> str:
        network = _CHAIN_NETWORK.get(chain, "eth-mainnet")
        return f"https://{network}.g.alchemy.com/v2/{self._key}"

    async def _post(self, chain: Chain, method: str, params: list) -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        resp = await self._client.post(self._url(chain), json=payload)
        if resp.status_code == 429:
            raise RateLimitError("Alchemy 429")
        if resp.status_code >= 400:
            raise ProviderError(f"Alchemy HTTP {resp.status_code}")
        body = resp.json()
        if "error" in body:
            raise ProviderError(str(body["error"]))
        return body.get("result", {})

    async def fetch_txs(self, address: str, chain: Chain, limit: int = 100) -> List[Transaction]:
        result = await self._post(
            chain,
            "alchemy_getAssetTransfers",
            [
                {
                    "fromAddress": address,
                    "category": ["external", "internal", "erc20"],
                    "maxCount": hex(limit),
                    "withMetadata": True,
                    "order": "desc",
                }
            ],
        )
        txns: List[Transaction] = []
        for item in result.get("transfers", []):
            try:
                ts_raw = item.get("metadata", {}).get("blockTimestamp", "1970-01-01T00:00:00Z")
                txns.append(
                    Transaction(
                        hash=item["hash"],
                        chain=chain,
                        block=int(item.get("blockNum", "0x0"), 16),
                        timestamp=datetime.fromisoformat(ts_raw.replace("Z", "+00:00")),
                        from_address=item.get("from", ""),
                        to_address=item.get("to"),
                        value=float(item.get("value") or 0),
                        value_usd=None,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("alchemy_tx_parse_error", error=str(exc))
        return txns

    async def fetch_balance(self, address: str, chain: Chain) -> float:
        result = await self._post(chain, "eth_getBalance", [address, "latest"])
        if isinstance(result, str):
            return int(result, 16) / 1e18
        return 0.0

    async def fetch_token_transfers(
        self, address: str, chain: Chain, limit: int = 100
    ) -> List[TokenTransfer]:
        result = await self._post(
            chain,
            "alchemy_getAssetTransfers",
            [
                {
                    "toAddress": address,
                    "category": ["erc20"],
                    "maxCount": hex(limit),
                    "withMetadata": False,
                    "order": "desc",
                }
            ],
        )
        transfers: List[TokenTransfer] = []
        for item in result.get("transfers", []):
            try:
                transfers.append(
                    TokenTransfer(
                        token_address=item.get("rawContract", {}).get("address", ""),
                        token_symbol=item.get("asset", "?"),
                        decimals=int(item.get("rawContract", {}).get("decimal", "0x12"), 16),
                        amount_raw=item.get("rawContract", {}).get("value", "0x0"),
                        amount_decimal=float(item.get("value") or 0),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("alchemy_token_parse_error", error=str(exc))
        return transfers
