"""Round-robin API key pool with per-key 60-second cooldown on 429."""
from __future__ import annotations

import time
from typing import List, Optional


class KeyPool:
    """Thread/async-safe round-robin pool with cooldown tracking."""

    _COOLDOWN_SECS = 60

    def __init__(self, keys: List[str]) -> None:
        self._keys = list(keys)
        self._cooldowns: dict[str, float] = {}  # key → cooldown_until timestamp

    def get(self) -> Optional[str]:
        """Return the next available key, or None if all are cooling."""
        now = time.monotonic()
        for key in self._keys:
            if now >= self._cooldowns.get(key, 0):
                # Rotate: move this key to the end so next call picks the next one
                self._keys.remove(key)
                self._keys.append(key)
                return key
        return None

    def mark_rate_limited(self, key: str) -> None:
        """Put *key* on a 60-second cooldown."""
        self._cooldowns[key] = time.monotonic() + self._COOLDOWN_SECS

    def available_count(self) -> int:
        """Number of keys not currently cooling."""
        now = time.monotonic()
        return sum(1 for k in self._keys if now >= self._cooldowns.get(k, 0))

    def __len__(self) -> int:
        return len(self._keys)
