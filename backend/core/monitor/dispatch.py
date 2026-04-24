"""Alert dispatch: Discord, Telegram, and in-process pub/sub."""
import os
import httpx
import asyncio
from backend.models.alert import AlertEvent


async def notify(event: AlertEvent, pubsub_channel: str = None) -> None:
    """Fan out alert to Discord, Telegram, and WebSocket pub/sub if configured."""
    tasks = []

    # Discord
    discord_url = os.getenv("DISCORD_WEBHOOK_URL")
    if discord_url:
        tasks.append(_send_discord(discord_url, event))

    # Telegram
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token:
        tasks.append(_send_telegram(telegram_token, event))

    # Pub/sub for WebSocket
    if pubsub_channel:
        tasks.append(_publish_pubsub(pubsub_channel, event))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def _send_discord(webhook_url: str, event: AlertEvent) -> None:
    """Send Discord embed notification."""
    embed = {
        "title": f"Blockchain Alert: {event.address[:8]}...",
        "description": f"Chain: {event.chain}\nEvent: {event.event_type}\nValue: ${event.value_usd:.2f}",
        "fields": [
            {"name": "TX Hash", "value": event.tx_hash},
            {"name": "Block", "value": str(event.block)},
        ],
        "color": 16711680,  # red
    }
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json={"embeds": [embed]}, timeout=10)


async def _send_telegram(bot_token: str, event: AlertEvent) -> None:
    """Send Telegram message notification."""
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not chat_id:
        return

    message = f"""
🚨 **Blockchain Alert**
Address: `{event.address}`
Chain: {event.chain}
Type: {event.event_type}
Value: ${event.value_usd:.2f}
TX: {event.tx_hash}
Block: {event.block}
"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(
            url,
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )


async def _publish_pubsub(channel: str, event: AlertEvent) -> None:
    """Publish to in-process pub/sub for WebSocket broadcast."""
    # Placeholder: in a real implementation, push to Redis pub/sub
    # For now, just a stub
    pass
