"""Idempotent wallet and edge upserts via MERGE."""
from __future__ import annotations

import structlog
from neo4j import AsyncTransaction

from .queries import UPSERT_TX_EDGE, UPSERT_WALLET
from models.transaction import Edge
from models.wallet import Wallet

log = structlog.get_logger()


async def upsert_wallet(tx: AsyncTransaction, wallet: Wallet) -> None:
    """MERGE a Wallet node — idempotent."""
    await tx.run(
        UPSERT_WALLET,
        address=wallet.address,
        chain=wallet.chain.value,
        first_seen=wallet.first_seen.isoformat() if wallet.first_seen else None,
        last_seen=wallet.last_seen.isoformat() if wallet.last_seen else None,
        tx_count=wallet.tx_count,
        balance_usd=wallet.balance_usd,
        labels=wallet.labels,
        risk_score=wallet.risk_score,
        is_contract=wallet.is_contract,
        created_at_block=wallet.created_at_block,
    )
    log.debug("upserted_wallet", address=wallet.address)


async def upsert_edge(tx: AsyncTransaction, edge: Edge) -> None:
    """MERGE a SENT relationship between two wallets — idempotent."""
    await tx.run(
        UPSERT_TX_EDGE,
        src=edge.src,
        dst=edge.dst,
        chain=edge.chain.value,
        tx_hash=edge.tx_hash,
        block=edge.block,
        timestamp=edge.timestamp.isoformat(),
        value=edge.value,
        value_usd=edge.value_usd,
        token=edge.token,
    )
    log.debug("upserted_edge", tx_hash=edge.tx_hash)
