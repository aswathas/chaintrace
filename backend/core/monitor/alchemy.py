"""Alchemy Webhooks parser. Converts Alchemy wallet activity to AlertEvent."""
from backend.models.alert import AlertEvent


def parse_alchemy_webhook(payload: dict) -> AlertEvent:
    """Parse Alchemy wallet activity webhook. Returns AlertEvent."""
    # Alchemy activity object structure
    activity = payload.get("activity", [])
    if not activity:
        raise ValueError("No activity in Alchemy webhook")

    act = activity[0]  # Handle first activity
    return AlertEvent(
        source="alchemy",
        address=act.get("to"),  # recipient wallet
        chain=_chain_from_network(payload.get("network")),
        tx_hash=act.get("hash"),
        block=act.get("blockNum"),
        value_usd=float(act.get("value", 0)) * float(act.get("valueUsd", 0)),
        event_type="transfer",
        timestamp=act.get("timestamp"),
    )


def _chain_from_network(network: str) -> str:
    """Map Alchemy network string to chain name."""
    mapping = {
        "eth-mainnet": "ethereum",
        "eth-sepolia": "ethereum",
        "polygon-mainnet": "polygon",
        "polygon-mumbai": "polygon",
        "arb-mainnet": "arbitrum",
        "arb-sepolia": "arbitrum",
        "base-mainnet": "base",
        "base-sepolia": "base",
        "bnb-mainnet": "bnb",
        "bnb-testnet": "bnb",
        "solana-mainnet": "solana",
    }
    return mapping.get(network, network)
