"""Etherscan-family provider — routes to correct explorer per chain."""
from __future__ import annotations

from datetime import datetime
from typing import List

import httpx
import structlog

from .base import ProviderError, RateLimitError
from .rotator import KeyPool
from models.transaction import TokenTransfer, Transaction
from models.wallet import Chain

log = structlog.get_logger()

_BASE_URLS: dict[Chain, str] = {
    Chain.eth: "https://api.etherscan.io/api",
    Chain.polygon: "https://api.polygonscan.com/api",
    Chain.arb: "https://api.arbiscan.io/api",
    Chain.base: "https://api.basescan.org/api",
    Chain.bsc: "https://api.bscscan.com/api",
}


class EtherscanProvider:
    """Implements Provider against the Etherscan API family with key rotation."""

    def __init__(self, key_pool: KeyPool) -> None:
        self._pool = key_pool
        self._client = httpx.AsyncClient(timeout=30)

    def _get_key(self) -> str:
        key = self._pool.get()
        if key is None:
            from .base import ProviderExhausted
            raise ProviderExhausted("All Etherscan keys cooling")
        return key

    async def _get(self, chain: Chain, params: dict) -> dict:
        base = _BASE_URLS.get(chain)
        if base is None:
            raise ProviderError(f"Etherscan family does not support chain {chain}")
        key = self._get_key()
        params["apikey"] = key
        resp = await self._client.get(base, params=params)
        if resp.status_code == 429:
            self._pool.mark_rate_limited(key)
            raise RateLimitError("Etherscan 429")
        if resp.status_code >= 400:
            raise ProviderError(f"Etherscan HTTP {resp.status_code}")
        data = resp.json()
        if data.get("status") == "0" and data.get("message") not in ("No transactions found", "No records found"):
            raise ProviderError(f"Etherscan error: {data.get('result')}")
        return data

    async def fetch_txs(self, address: str, chain: Chain, limit: int = 100) -> List[Transaction]:
        data = await self._get(
            chain,
            {
                "module": "account",
                "action": "txlist",
                "address": address,
                "sort": "desc",
                "offset": limit,
                "page": 1,
            },
        )
        txns: List[Transaction] = []
        for item in data.get("result", []) or []:
            try:
                txns.append(
                    Transaction(
                        hash=item["hash"],
                        chain=chain,
                        block=int(item["blockNumber"]),
                        timestamp=datetime.utcfromtimestamp(int(item["timeStamp"])),
                        from_address=item.get("from", ""),
                        to_address=item.get("to") or None,
                        value=int(item.get("value", "0")) / 1e18,
                        gas_used=int(item.get("gasUsed", 0)),
                        gas_price=int(item.get("gasPrice", 0)),
                        method_id=item.get("methodId"),
                        is_success=item.get("isError", "0") == "0",
                    )
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("etherscan_tx_parse_error", error=str(exc))
        return txns

    async def fetch_balance(self, address: str, chain: Chain) -> float:
        data = await self._get(
            chain,
            {"module": "account", "action": "balance", "address": address, "tag": "latest"},
        )
        return int(data.get("result", "0")) / 1e18

    async def fetch_token_transfers(
        self, address: str, chain: Chain, limit: int = 100
    ) -> List[TokenTransfer]:
        data = await self._get(
            chain,
            {
                "module": "account",
                "action": "tokentx",
                "address": address,
                "sort": "desc",
                "offset": limit,
                "page": 1,
            },
        )
        transfers: List[TokenTransfer] = []
        for item in data.get("result", []) or []:
            try:
                decimals = int(item.get("tokenDecimal", 18))
                raw = item.get("value", "0")
                dec = int(raw) / 10**decimals
                transfers.append(
                    TokenTransfer(
                        token_address=item.get("contractAddress", ""),
                        token_symbol=item.get("tokenSymbol", "?"),
                        decimals=decimals,
                        amount_raw=raw,
                        amount_decimal=dec,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("etherscan_token_parse_error", error=str(exc))
        return transfers
