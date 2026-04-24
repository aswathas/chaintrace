# Labeler Module

**Location:** `backend/core/labeler/`

## Purpose

Priority-ordered label resolution from six sources: hardcoded registries, community repos, Etherscan tags, Arkham free API, user submissions, and heuristic inference. Returns winning label and full provenance chain.

## Public API

### `merge.py`

**`resolve_label(address: str, chain: str = "ethereum", wallet: Optional[dict] = None, behavior: Optional[dict] = None, outflows: Optional[list] = None, inflows: Optional[list] = None) -> LabelBundle`**
Async entry point. Calls all six sources in priority order. Returns `LabelBundle` with winner + provenance.

**`LabelBundle`** (dataclass)
```python
address: str
winner: Optional[Label]         # highest-priority non-null label
provenance: list[Label]         # all non-null results
source_order: list[str]         # ["hardcoded", "community", ..., "heuristic"]
```

### `hardcoded.py`

Highest-confidence pre-curated mappings. Module-level dict `HARDCODED_LABELS` (lowercase address → label string).

**Included registries:**
- `TORNADO_POOLS` — address → f"tornado_cash_{denom}eth"
- `BRIDGE_CONTRACTS` — address → bridge name (Stargate, Wormhole, LayerZero, etc.)
- `CEX_HOT_WALLETS` — address → exchange name (Binance, Coinbase, Kraken, Bitfinex, OKX, Bybit)
- `EXPLOIT_WALLETS` — address → incident label (Ronin, Harmony, Nomad, Wormhole)
- `DEX_ROUTERS` — address → router name (Uniswap v2/v3, SushiSwap, 1inch, Curve, Balancer, Paraswap)
- `EXPLOIT_REGISTRY` — rich metadata dict (label, incident, date, stolen_usd)

**~80 addresses total hardcoded.**

### `community.py`

**`load_community_labels() -> dict[str, Label]`**
Async. Load Postgres snapshot of community repos: `brianleect/etherscan-labels`, `dawsbot/eth-labels`. Currently stubbed (TODO: Postgres wiring).

Returns mapping of address → `Label(address, label, source="community", confidence)`.

### `etherscan.py`

**`scrape_etherscan_tag(address: str, chain: str) -> Optional[Label]`**
Async. Fetch public address tag from Etherscan API. Cached 1h in Redis. Currently stubbed (TODO: httpx + Redis wiring).

Returns `Label` with source="etherscan" and confidence ~0.7 (public tags are crowd-sourced).

### `arkham.py`

**`fetch_arkham_label(address: str) -> Optional[Label]`**
Async. Query Arkham Intelligence free API. Cached 1h. Currently stubbed (TODO: httpx + Redis wiring).

Returns `Label` with source="arkham" and confidence ~0.8.

### `submissions.py`

**`get_user_labels(address: str) -> list[Label]`**
Async. Fetch user-submitted labels from Postgres table `submitted_labels`, ordered by creation date (newest first). Currently stubbed (TODO: Postgres wiring).

Returns list of `Label(source="submissions", confidence=varies)`. Newest first so first() = highest-priority submission.

### `heuristic.py`

**`infer_label(wallet: dict, behavior: dict, outflows: Optional[list], inflows: Optional[list]) -> Optional[Label]`**
Lowest-priority heuristic inference. Examples:
- "wallet sent to 50+ unique recipients, equal amounts" → `airdrop_distributor`
- "received from Binance hot, then distributed" → `binance_user_wallet`
- "all txs to same contract with same amount" → `bot_activity`

Returns `Label(source="heuristic", confidence ~0.4)` or None.

**Label dataclass (imported from community.py or defined locally):**
```python
address: str
label: str
source: str                 # "hardcoded" | "community" | "etherscan" | "arkham" | "submissions" | "heuristic"
confidence: float           # 0.0–1.0
```

## Algorithm & Data Flow

```
resolve_label(address, chain, wallet, behavior, outflows, inflows)
├─ addr_lower = address.lower()
├─ Source 1 (hardcoded):
│  ├─ lookup HARDCODED_LABELS[addr_lower]
│  └─ if found: Label(confidence=1.0), set winner
├─ Source 2 (community):
│  ├─ await load_community_labels()
│  └─ if found: append to provenance, set winner if no hardcoded
├─ Source 3 (etherscan):
│  ├─ await scrape_etherscan_tag(address, chain)
│  └─ if found: append, set winner if no prior
├─ Source 4 (arkham):
│  ├─ await fetch_arkham_label(address)
│  └─ if found: append, set winner if no prior
├─ Source 5 (submissions):
│  ├─ await get_user_labels(address)
│  └─ if found: append all, set winner to first if no prior
└─ Source 6 (heuristic):
   ├─ if wallet provided: infer_label(wallet, behavior, outflows, inflows)
   └─ if found: append, set winner if all prior null
└─ return LabelBundle(address, winner, provenance, source_order)
```

## Dependencies

**Imports:**
- `.hardcoded`, `.community`, `.etherscan`, `.arkham`, `.submissions`, `.heuristic` — local label sources

**Imported by:**
- `backend.api.routes.labels` — GET `/labels/{address}`
- `backend.core.tracer.engine` — label resolution during traversal (TODO)
- `backend.core.profiler.scorer` — label lookup during risk scoring

## Extension Points

1. **Add new label source:** Implement async function returning `Optional[Label]`, add to `resolve_label()` in priority order.
2. **Adjust source priority:** Reorder sources in `resolve_label()`.
3. **Adjust confidence scores:** Tune per-source `confidence` values.
4. **Heuristic expansion:** Add new pattern detection in `heuristic.py`.

## Testing Guidance

**Unit tests:**
- Mock all six sources and verify priority order (hardcoded always wins on tie)
- Verify `LabelBundle.winner` is correct when sources return conflicting labels
- Verify `provenance` contains all non-null results in correct order
- Test edge case: all sources return None (winner should be None)
- Test case-insensitivity (lowercase lookup)

**Integration:**
- Test hardcoded labels for known addresses (Tornado pools, Binance hot wallets, known exploits)
- Verify Redis cache hit for Etherscan/Arkham after first fetch
- Verify community label loading from mock Postgres
- Test heuristic inference with synthetic wallet data

## Known Gaps & TODOs

- `community.py` — Postgres fetch stubbed; needs migration to load_community_labels table
- `etherscan.py:15` — httpx wiring TODO
- `etherscan.py:9` — Redis cache wiring TODO
- `arkham.py:20` — httpx wiring TODO
- `arkham.py:8` — Redis cache wiring TODO
- `submissions.py:4` — Postgres wiring TODO
- No rate-limit handling for Etherscan/Arkham APIs
- No auto-refresh of community repo snapshot (manual cron needed per spec)

## See Also

- `tracer.md` — uses labels during terminal classification
- `profiler.md` — uses labels during risk scoring
- `data-cache.md` — Redis storage for label caching
