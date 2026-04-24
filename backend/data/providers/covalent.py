"""Covalent (GoldRush) v1 API provider — 100+ chains unified."""
from __future__ import annotations

from datetime import datetime
from typing import List

import httpx
import structlog

from .base import ProviderError, RateLimitError
from models.transaction import TokenTransfer, Transaction
from models.wallet import Chain

log = structlog.get_logger()

_CHAIN_IDS: dict[Chain, str] = {
    Chain.eth: "eth-mainnet",
    Chain.polygon: "matic-mainnet",
    Chain.arb: "arbitrum-mainnet",
    Chain.base: "base-mainnet",
    Chain.bsc: "bsc-mainnet",
    Chain.solana: "solana-mainnet",
}

_BASE = "https://api.covalenthq.com/v1"


class CovalentProvider:
    """Implements Provider using the Covalent GoldRush API."""

    def __init__(self, api_key: str) -> None:
        self._key = api_key
        self._client = httpx.AsyncClient(timeout=30)

    async def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{_BASE}{path}"
        resp = await self._client.get(url, params=params, auth=(self._key, ""))
        if resp.status_code == 429:
            raise RateLimitError("Covalent 429")
        if resp.status_code >= 400:
            raise ProviderError(f"Covalent HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if data.get("error"):
            raise ProviderError(data.get("error_message", "unknown"))
        return data

    async def fetch_txs(self, address: str, chain: Chain, limit: int = 100) -> List[Transaction]:
        chain_id = _CHAIN_IDS.get(chain, "eth-mainnet")
        data = await self._get(
            f"/{chain_id}/address/{address}/transactions_v3/",
            {"page-size": limit},
        )
        txns: List[Transaction] = []
        items = data.get("data", {}).get("items", [])
        for item in items:
            try:
                txns.append(
                    Transaction(
                        hash=item["tx_hash"],
                        chain=chain,
                        block=item["block_height"],
                        timestamp=datetime.fromisoformat(item["block_signed_at"].replace("Z", "+00:00")),
                        from_address=item.get("from_address", ""),
                        to_address=item.get("to_address"),
                        value=float(item.get("value_quote", 0) or 0),
                        value_usd=item.get("value_quote"),
                        gas_used=item.get("gas_spent"),
                        gas_price=item.get("gas_price"),
                        is_success=item.get("successful", True),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("covalent_tx_parse_error", error=str(exc))
        return txns

    async def fetch_balance(self, address: str, chain: Chain) -> float:
        chain_id = _CHAIN_IDS.get(chain, "eth-mainnet")
        data = await self._get(f"/{chain_id}/address/{address}/balances_v2/")
        items = data.get("data", {}).get("items", [])
        # Return balance of the native token (contract_address == None)
        for item in items:
            if not item.get("contract_address"):
                return float(item.get("balance", 0)) / 10 ** int(item.get("contract_decimals", 18))
        return 0.0

    async def fetch_token_transfers(
        self, address: str, chain: Chain, limit: int = 100
    ) -> List[TokenTransfer]:
        # Reuse balances endpoint — each item is a token holding
        chain_id = _CHAIN_IDS.get(chain, "eth-mainnet")
        data = await self._get(f"/{chain_id}/address/{address}/balances_v2/")
        transfers: List[TokenTransfer] = []
        for item in data.get("data", {}).get("items", []):
            if not item.get("contract_address"):
                continue  # skip native
            decimals = int(item.get("contract_decimals", 18))
            raw = str(item.get("balance", "0"))
            try:
                dec = float(raw) / 10**decimals
            except Exception:  # noqa: BLE001
                dec = 0.0
            transfers.append(
                TokenTransfer(
                    token_address=item["contract_address"],
                    token_symbol=item.get("contract_ticker_symbol", "?"),
                    decimals=decimals,
                    amount_raw=raw,
                    amount_decimal=dec,
                    value_usd=item.get("quote"),
                )
            )
        return transfers
