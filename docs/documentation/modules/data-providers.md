# Data Providers Module

**Location:** `backend/data/providers/`

## Purpose

Abstract blockchain data ingestion behind a provider protocol with automatic fallback, API key rotation, and rate-limit handling. Implement Covalent, Alchemy, Etherscan family, The Graph, and public RPC adapters.

## Public API

### `base.py`

**`Provider` (Protocol, runtime_checkable)**
Async interface that all providers implement.

```python
async def fetch_txs(address: str, chain: Chain, limit: int = 100) -> List[Transaction]
async def fetch_balance(address: str, chain: Chain) -> float
async def fetch_token_transfers(address: str, chain: Chain, limit: int = 100) -> List[TokenTransfer]
```

**Exceptions:**
- `ProviderError` — base error
- `RateLimitError` — HTTP 429
- `ProviderExhausted` — all keys/retries exhausted

### `rotator.py`

**`KeyPool(keys: List[str])`**
Thread/async-safe round-robin pool with per-key 60-second cooldown on rate limit.

**Methods:**
- `get() -> Optional[str]` — Return next available key; rotate to end. None if all cooling.
- `mark_rate_limited(key: str)` — Put key on 60s cooldown.
- `available_count() -> int` — Count of non-cooling keys.
- `__len__() -> int` — Total key count.

**Usage:**
```python
pool = KeyPool(["key1", "key2", "key3"])
while True:
    key = pool.get()
    if not key:
        break  # all cooling
    try:
        await provider.fetch(key)
    except RateLimitError:
        pool.mark_rate_limited(key)
```

### `fallback.py` (integrator)

**`FallbackChain` (orchestrator)**
Manages provider chain: `Covalent → Alchemy → Etherscan → Public RPC`.

**Methods:**
- `async fetch_txs(address: str) -> List[Transaction]` — Try each provider in order until success or all exhausted.
- `async fetch_balance(address: str) -> float` — Ditto.
- `async find_bridge_mint(...) -> Optional[dict]` — Cross-chain bridge matching (Covalent/Alchemy specific).

**Behavior:**
- On `RateLimitError` → rotate key in provider's pool, retry
- On other error → escalate to next provider
- Return cached result with `stale=true` if all providers fail

**Return type:** `{"value": float, "recipient": str, "tx_hash": str, ...}` (and similar for other methods).

### Provider implementations

**`covalent.py` — Covalent API (goldrush.dev)**
- **Chains:** 100+ EVM chains + Solana (unified)
- **API:** `/v1/address/{address}/transactions_v2/`
- **Cost:** ~1 credit per address
- **Rate limit:** 10 req/sec on free tier
- **Strength:** Unified multi-chain interface

**`alchemy.py` — Alchemy API (alchemy.com)**
- **Chains:** Ethereum, Polygon, Arbitrum, Base, Optimism, Solana
- **API:** `eth_getAssetTransfers` (getAssets method)
- **Cost:** Free tier (1M cu/month)
- **Rate limit:** 350 req/sec on free tier
- **Strength:** Fast, high rate limit

**`etherscan.py` — Etherscan family (per-chain)**
- **Implementations:** Etherscan (ETH), Polygonscan, Arbiscan, Basescan, BscScan
- **API:** `/api?module=account&action=txlist`
- **Cost:** Free tier (5 req/sec per key)
- **Rate limit:** Pool 5+ keys → 25 req/sec
- **Strength:** Reliable, per-key rotation built-in

**`thegraph.py` — The Graph Protocol**
- **Chains:** Decentralized subgraph queries (Uniswap, Aave, Curve, bridges)
- **API:** GraphQL endpoint per subgraph
- **Cost:** Free (decentralized, no API key)
- **Rate limit:** Reasonable (no strict limit, but query complexity)
- **Strength:** DeFi protocol data only; free, no rate limit

**`rpc.py` — Public RPC (chainlist.org)**
- **Chains:** All EVM (Ethereum, Polygon, Arbitrum, Base, Optimism, BNB, etc.)
- **API:** JSON-RPC standard (`eth_call`, `eth_getLogs`, etc.)
- **Cost:** Free (public endpoints)
- **Rate limit:** Varies by public RPC; usually loose on major providers
- **Strength:** Fallback when all paid providers exhausted

## Algorithm & Data Flow

```
FallbackChain.fetch_txs(address, chain)
├─ for provider in [Covalent, Alchemy, Etherscan, PublicRPC]:
│  ├─ try:
│  │  ├─ if provider uses KeyPool:
│  │  │  ├─ key = pool.get()
│  │  │  ├─ if not key: continue to next provider
│  │  ├─ result = await provider.fetch_txs(address, chain)
│  │  └─ return result
│  ├─ except RateLimitError:
│  │  ├─ pool.mark_rate_limited(key) [if applicable]
│  │  └─ continue to next provider
│  ├─ except ProviderError:
│  │  └─ continue to next provider
│  └─ except other error:
│     └─ log, continue to next provider
├─ if all failed: return cached_result with stale=True
└─ raise ProviderExhausted

KeyPool.get()
├─ for each key in pool:
│  ├─ if now >= cooldown_until[key]:
│  │  ├─ rotate key to end
│  │  └─ return key
├─ return None (all cooling)
```

## Dependencies

**Imports:**
- `httpx` — async HTTP for Covalent, Alchemy, Etherscan, Arkham
- `redis.asyncio` — caching (when available)
- `models.transaction`, `models.wallet` — data types
- `.rotator` — KeyPool

**Imported by:**
- `backend.core.tracer.engine` — `_get_outflows()` (TODO)
- `backend.core.tracer.cross_chain` — `match_bridge_out()` (TODO)
- `backend.core.tracer.mixer_exit` — `match_tornado_exits()` (TODO)
- API routes — direct or via FallbackChain

## Extension Points

1. **Add new provider:** Implement `fetch_txs()`, `fetch_balance()`, `fetch_token_transfers()` per protocol. Register in `FallbackChain`.
2. **Adjust fallback order:** Reorder providers in `FallbackChain.fetch_txs()`.
3. **Key pool sizing:** Modify `KeyPool.__init__()` to accept per-provider key lists.
4. **Cooldown duration:** Change `_COOLDOWN_SECS = 60` in `rotator.py`.
5. **Caching strategy:** Integrate `backend.data.cache.RedisCache` per provider.

## Testing Guidance

**Unit tests:**
- Mock each provider's HTTP response; verify correct parsing
- Verify KeyPool round-robin and cooldown logic
- Test FallbackChain fallover on RateLimitError
- Test all providers exhausted → stale cache return

**Integration:**
- Run against testnet with real API keys
- Verify Covalent multi-chain (Ethereum + Polygon + Arbitrum)
- Verify Alchemy high-frequency use (Solana txs)
- Verify Etherscan pool of 5 keys
- Verify bridge mint detection via Alchemy
- Verify The Graph Uniswap swap history

## Known Gaps & TODOs

- `covalent.py`, `alchemy.py`, `etherscan.py`, `thegraph.py`, `rpc.py` — implementations likely stubbed or incomplete
- No explicit Redis caching in provider implementations (TODO)
- `fallback.py` — orchestrator may be incomplete or missing bridge-specific routing
- No metrics/observability on key cooldowns or provider failures
- No weighted fallback (some providers faster/cheaper than others)
- Solana support in rpc.py (different JSON-RPC namespace)

## See Also

- `data-cache.md` — caching layer for provider results
- `data-graph.md` — Neo4j upsert for provider-fetched data
- `tracer.md` — uses providers via FallbackChain
- `labeler.md` — uses Etherscan/Arkham providers
