# Data Cache Module

**Location:** `backend/data/cache/`

## Purpose

Async Redis wrapper with TTL policy. Stores transactions, balances, labels, profiles, traces with age-aware expiry: old txs cached forever, recent txs 5-minute TTL, balances 30 seconds, labels 1 hour.

## Public API

### `redis_cache.py`

**`RedisCache(client: aioredis.Redis)`**
Thin async wrapper around redis-py with JSON serialization.

**Methods:**
- `async get(key: str) -> Optional[Any]` — Fetch and deserialize JSON.
- `async set(key: str, value: Any, ttl: Optional[int] = None) -> None` — Serialize and store. If ttl=None, no expiry.
- `async delete(key: str) -> None` — Remove key.
- `async exists(key: str) -> bool` — Check existence.
- `async ping() -> bool` — Health check; returns False on error.

**Serialization:** `json.dumps(value, default=str)` — converts non-JSON objects via `str()`.

### `keys.py`

**`KeyType` (Enum)**
```python
tx = "tx"
wallet_txs = "wallet_txs"
balance = "balance"
label = "label"
profile = "profile"
trace = "trace"
```

**`ttl_for(key_type: KeyType, block_age_blocks: int = 0) -> Optional[int]`**
Return TTL in seconds or None (permanent). Logic:
- `balance` → 30s
- `label` → 3600s (1 hour)
- `tx` or `wallet_txs` → if block age ≥ 1000: None (permanent); else 300s (5 min)
- `profile` → 600s (10 min)
- default → 300s

**Reasoning:** Blocks older than 1000 (~4 hours on Ethereum) are immutable; cache permanently. Recent blocks may be reorganized; short 5-minute TTL.

## Algorithm & Data Flow

```
Usage pattern (from tracer/labeler/profiler):

set_cached_tx(tx_hash, tx_data, block_age):
├─ key = f"tx:{tx_hash}"
├─ ttl = ttl_for(KeyType.tx, block_age)
└─ await cache.set(key, tx_data, ttl)

get_cached_tx(tx_hash):
├─ key = f"tx:{tx_hash}"
├─ result = await cache.get(key)
└─ return result or None

get_cached_balance(address, chain):
├─ key = f"balance:{chain}:{address.lower()}"
├─ result = await cache.get(key)
└─ return result or None

set_cached_label(address, label_bundle):
├─ key = f"label:{address.lower()}"
├─ ttl = ttl_for(KeyType.label)
└─ await cache.set(key, label_bundle.__dict__, ttl)
```

## Dependencies

**Imports:**
- `redis.asyncio` — async Redis client
- `json`, `enum` — serialization, type hints

**Imported by:**
- `backend.core.labeler.etherscan` — cache Etherscan tags (TODO)
- `backend.core.labeler.arkham` — cache Arkham labels (TODO)
- `backend.data.providers.*` — cache provider results (TODO)
- Any async route needing memoization

## Extension Points

1. **Add key type:** Append to `KeyType` enum; add branch to `ttl_for()`.
2. **Adjust TTLs:** Modify constants at top of `redis_cache.py`.
3. **Cache key schema:** Design naming convention (e.g., `"{type}:{chain}:{address_or_hash}"`) and document in `keys.py`.
4. **Serialization hooks:** Enhance `json.dumps(..., default=str)` to handle custom types (Dataclasses, enums).

## Testing Guidance

**Unit tests:**
- Set and get JSON-serializable objects
- Verify TTL application (set with ttl → check Redis PTTL)
- Verify no-expiry for old txs (set with ttl=None → no expiry)
- Test ping() failure returns False
- Test JSON serialization of complex objects (datetime, enums)

**Integration:**
- Run against real Redis instance
- Set tx with young block age → verify 300s TTL
- Set tx with old block age → verify no expiry
- Set label → verify 3600s TTL
- Set balance → verify 30s TTL
- Verify key expiry by waiting and checking existence

## Known Gaps & TODOs

- No key patterns/scan support (can't bulk clear cache by prefix)
- No compression (large traces may be expensive to store)
- No distributed cache invalidation (single Redis instance assumed)
- Serialization of custom types may produce verbose output (dataclasses → dict)
- No metrics on cache hit/miss rates

## See Also

- `data-providers.md` — should integrate caching in fetch methods
- `labeler.md` — uses cache for label TTL
