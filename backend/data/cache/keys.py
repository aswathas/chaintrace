"""Cache key builders for consistent Redis key naming."""
from __future__ import annotations


def tx_key(chain: str, tx_hash: str) -> str:
    return f"tx:{chain}:{tx_hash.lower()}"


def wallet_txs_key(chain: str, address: str) -> str:
    return f"wallet_txs:{chain}:{address.lower()}"


def balance_key(chain: str, address: str) -> str:
    return f"balance:{chain}:{address.lower()}"


def label_key(address: str) -> str:
    return f"label:{address.lower()}"


def profile_key(chain: str, address: str) -> str:
    return f"profile:{chain}:{address.lower()}"


def trace_key(job_id: str) -> str:
    return f"trace:{job_id}"
