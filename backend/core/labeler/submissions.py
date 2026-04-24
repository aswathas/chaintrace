"""User-submitted labels from Postgres `submitted_labels` table — source 5."""
from __future__ import annotations

from .community import Label


async def get_user_labels(address: str) -> list[Label]:
    """Return all user-submitted labels for an address, newest first."""
    addr_lower = address.lower()
    # TODO: wire to backend.data.db.postgres when available
    # rows = await postgres.fetch_all(
    #     """SELECT address, label, source, confidence
    #        FROM submitted_labels
    #        WHERE LOWER(address) = $1 AND reviewed = TRUE
    #        ORDER BY created_at DESC""",
    #     addr_lower,
    # )
    # return [Label(
    #     address=row["address"],
    #     label=row["label"],
    #     source=f"user_submission:{row['source']}",
    #     confidence=row["confidence"],
    # ) for row in rows]
    return []  # placeholder until Postgres layer wired
