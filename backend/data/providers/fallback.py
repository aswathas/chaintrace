"""Provider chain orchestrator — walks the fallback list on exhaustion."""
from __future__ import annotations

import structlog
from typing import Any, Callable, List, Optional, TypeVar

from .base import Provider, ProviderError, ProviderExhausted, RateLimitError
from models.wallet import Chain

log = structlog.get_logger()
T = TypeVar("T")


class FallbackChain:
    """Try providers in order; on exhaustion move to the next."""

    def __init__(self, providers: List[Provider]) -> None:
        self._providers = providers

    async def _call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        last_err: Optional[Exception] = None
        for provider in self._providers:
            fn: Callable[..., Any] = getattr(provider, method)
            try:
                result = await fn(*args, **kwargs)
                return result
            except ProviderExhausted as exc:
                log.warning("provider_exhausted", provider=type(provider).__name__, method=method)
                last_err = exc
            except RateLimitError as exc:
                log.warning("rate_limit", provider=type(provider).__name__, method=method)
                last_err = exc
            except ProviderError as exc:
                log.warning("provider_error", provider=type(provider).__name__, method=method, error=str(exc))
                last_err = exc
        raise ProviderExhausted(f"All providers exhausted for {method}") from last_err

    async def fetch_txs(self, address: str, chain: Chain, limit: int = 100) -> Any:
        return await self._call("fetch_txs", address, chain, limit)

    async def fetch_balance(self, address: str, chain: Chain) -> Any:
        return await self._call("fetch_balance", address, chain)

    async def fetch_token_transfers(self, address: str, chain: Chain, limit: int = 100) -> Any:
        return await self._call("fetch_token_transfers", address, chain, limit)
