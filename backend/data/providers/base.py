"""Provider protocol and shared exceptions."""
from __future__ import annotations

from typing import Any, List, Protocol, runtime_checkable

from models.transaction import TokenTransfer, Transaction
from models.wallet import Chain


class ProviderError(Exception):
    """Base error for provider failures."""


class RateLimitError(ProviderError):
    """HTTP 429 received from provider."""


class ProviderExhausted(ProviderError):
    """All keys / retries for this provider are exhausted."""


@runtime_checkable
class Provider(Protocol):
    """Async blockchain data provider contract."""

    async def fetch_txs(
        self,
        address: str,
        chain: Chain,
        limit: int = 100,
    ) -> List[Transaction]:
        """Return a list of transactions involving *address*."""
        ...

    async def fetch_balance(
        self,
        address: str,
        chain: Chain,
    ) -> float:
        """Return native-token balance in human-readable units."""
        ...

    async def fetch_token_transfers(
        self,
        address: str,
        chain: Chain,
        limit: int = 100,
    ) -> List[TokenTransfer]:
        """Return ERC-20 / SPL token transfers for *address*."""
        ...
