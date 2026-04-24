"""Etherscan public address tag scraper — source 3 of the label pipeline."""
from __future__ import annotations

import re
from typing import Optional

from .community import Label

ETHERSCAN_TAG_URLS: dict[str, str] = {
    "ethereum": "https://etherscan.io/address/{address}",
    "polygon": "https://polygonscan.com/address/{address}",
    "arbitrum": "https://arbiscan.io/address/{address}",
    "base": "https://basescan.org/address/{address}",
    "bsc": "https://bscscan.com/address/{address}",
}

# Regex to extract the public name tag from Etherscan HTML
_TAG_PATTERN = re.compile(
    r'<span[^>]+class="[^"]*u-label[^"]*"[^>]*>\s*([^<]+)\s*</span>',
    re.IGNORECASE,
)


async def scrape_etherscan_tag(address: str, chain: str = "ethereum") -> Optional[Label]:
    """Fetch the Etherscan public tag for an address; cache-aware via backend.data.cache."""
    chain_key = chain.lower()
    url_template = ETHERSCAN_TAG_URLS.get(chain_key)
    if not url_template:
        return None

    url = url_template.format(address=address)
    cache_key = f"etherscan_tag:{chain_key}:{address.lower()}"

    # TODO: wire to backend.data.cache.redis_cache when available
    # cached = await redis_cache.get(cache_key)
    # if cached:
    #     return Label(**cached) if cached != "null" else None
    cached = None

    # TODO: wire to httpx when available
    # async with httpx.AsyncClient(timeout=10) as client:
    #     try:
    #         resp = await client.get(url, headers={"User-Agent": "ChainTrace/1.0"})
    #         resp.raise_for_status()
    #         html = resp.text
    #     except Exception:
    #         return None
    html: Optional[str] = None  # placeholder until httpx wired

    if html is None:
        return None

    match = _TAG_PATTERN.search(html)
    if not match:
        # TODO: cache negative result: await redis_cache.set(cache_key, "null", ttl=3600)
        return None

    tag_text = match.group(1).strip()
    label = Label(address=address.lower(), label=tag_text, source="etherscan", confidence=0.85)

    # TODO: cache positive result: await redis_cache.set(cache_key, label.__dict__, ttl=3600)
    return label
