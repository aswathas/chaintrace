"""Community label loader — reads from Postgres table `community_labels`.

Weekly cron (implemented in backend/workers/label_sync_job.py):
  - Clone/pull brianleect/etherscan-labels and dawsbot/eth-labels from GitHub.
  - Parse their JSON/CSV files into {address: label} mappings.
  - Upsert into Postgres table `community_labels(address, label, source, updated_at)`.
The cron is NOT implemented here; this module only reads the already-synced data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Label:
    address: str
    label: str
    source: str
    confidence: float = 1.0


async def load_community_labels() -> dict[str, Label]:
    """Return {lowercase_address: Label} from Postgres community_labels table."""
    # TODO: wire to backend.data.db.postgres when available
    # rows = await postgres.fetch_all(
    #     "SELECT address, label, source FROM community_labels"
    # )
    # return {row["address"].lower(): Label(
    #     address=row["address"],
    #     label=row["label"],
    #     source=row["source"],
    # ) for row in rows}
    return {}  # placeholder until Postgres layer wired
