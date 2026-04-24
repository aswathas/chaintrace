"""Moralis Streams parser. Converts Moralis transaction to AlertEvent."""
from backend.models.alert import AlertEvent


def parse_moralis_webhook(payload: dict) -> AlertEvent:
    """Parse Moralis Stream webhook. Returns AlertEvent."""
    # Moralis Stream structure
    result = payload.get("result", {})
    return AlertEvent(
        source="moralis",
        address=result.get("to_address"),
        chain=result.get("chain"),
        tx_hash=result.get("transaction_hash"),
        block=result.get("block_number"),
        value_usd=float(result.get("value", 0)) / 1e18,  # wei to eth
        event_type=result.get("transaction_type", "transfer"),
        timestamp=result.get("block_timestamp"),
    )
