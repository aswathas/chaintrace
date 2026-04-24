# Tracer Module

**Location:** `backend/core/tracer/`

## Purpose

Implements hop-by-hop fund flow traversal using breadth-first search (BFS). Given a seed wallet or transaction, the tracer follows outflows across chains, identifying terminal destinations (CEX deposits, mixers, bridges, cold storage) and probabilistically matching Tornado Cash mixer exits.

## Public API

### `engine.py`

**`trace(seed_address: str, chain: str, max_hops: int = 10, min_value_usd: float = 100.0, fanout: int = 5) -> TraceResult`**
Traverse fund flows from a seed address via BFS. Returns graph of visited wallets, edges, and detected terminals. Limits to 500 wallets to prevent explosion; fan-out to top-5 values per hop.

**`TraceResult`** (dataclass)
```python
seed: str
chain: str
nodes: list[HopNode]        # visited wallets with terminal classification
edges: list[OutflowEdge]    # transactions
terminals: list[tuple[OutflowEdge, Terminal]]
visited_count: int
truncated: bool             # True if MAX_WALLETS hit
started_at: datetime
finished_at: Optional[datetime]
```

**`HopNode`** (dataclass)
Wallet address at a depth with optional terminal marker and mixer exit candidates.

**`OutflowEdge`** (dataclass)
Transaction representation: src/dst addresses, chain, tx_hash, value_usd, block, timestamp, gas_price_gwei.

### `terminals.py`

**`classify_terminal(address: str, labels: dict[str, str] | None = None) -> Optional[Terminal]`**
Classify a destination as CEX, mixer, bridge, or None. Checks hardcoded registries first, then caller-supplied labels.

**`Terminal`** (dataclass)
```python
kind: str                   # "cex" | "mixer" | "bridge" | "cold_storage"
label: str                  # human-readable: "tornado_cash_1eth", "binance", etc.
address: str
denomination: Optional[float]  # for mixer only
```

**`is_cold_storage(address: str, last_outflow_ts: Optional[datetime], balance_usd: float) -> bool`**
Heuristic: no outflows in 180 days and positive balance.

**Registries (module-level dicts):**
- `TORNADO_POOLS` — address → denomination (0.1/1/10/100 ETH)
- `BRIDGE_CONTRACTS` — address → bridge name (Stargate, Wormhole, etc.)
- `CEX_HOT_WALLETS` — address → exchange name (Binance, Coinbase, etc.)
- `EXPLOIT_WALLETS` — address → incident label (Ronin, Harmony, etc.)

### `cross_chain.py`

**`match_bridge_out(deposit: BridgeEdge) -> Optional[str]`**
Given a bridge deposit, search destination chain for mint event matching value ±0.5% and timestamp ±30 minutes. Returns recipient address on dest chain or None. Currently stubbed (TODO).

**`BridgeEdge`** (dataclass)
Minimal bridge deposit representation: src, dst (bridge contract), chain, tx_hash, timestamp, value_usd, token, dst_chain (optional).

### `mixer_exit.py`

**`match_tornado_exits(deposit_tx: DepositTx, deposit_gas_gwei: Optional[float]) -> list[MixerExitCandidate]`**
Scan Tornado withdrawals of same denomination in 72-hour window. Rank by composite score: timing (40%), gas price match (35%), recipient behavior (25%). All candidates marked `unconfirmed=True`.

**`MixerExitCandidate`** (dataclass)
```python
recipient: str
tx_hash: str
timestamp: int
denomination: float
confidence: float           # 0–1, composite score
unconfirmed: bool = True
timing_score: float
gas_score: float
behavior_score: float
```

**Scoring functions:**
- `_timing_score(deposit_ts: int, withdrawal_ts: int) -> float` — Gaussian decay over 72h
- `_gas_score(deposit_gas: Optional[float], withdrawal_gas: float) -> float` — Ratio similarity
- `_behavior_score(recipient_behavior: Optional[dict]) -> float` — Behavioral heuristics

## Algorithm & Data Flow

```
trace(seed, chain, max_hops, min_value_usd, fanout)
├─ frontier = deque([(seed, chain, 0, None)])
├─ visited = set()
├─ while frontier and len(visited) < MAX_WALLETS (500):
│  ├─ pop (address, chain, depth, parent_edge)
│  ├─ if visited or depth > max_hops: skip
│  ├─ get_outflows(address, chain)  [Neo4j-first, then providers]
│  ├─ filter by min_value_usd
│  ├─ split into top_n (fanout=5) and rest
│  ├─ for each top outflow:
│  │  ├─ classify_terminal(dst)
│  │  ├─ if mixer:
│  │  │  └─ match_tornado_exits() → add MixerExitCandidates
│  │  ├─ if bridge:
│  │  │  └─ match_bridge_out() → enqueue cross-chain hop
│  │  └─ else: enqueue to frontier
│  └─ append HopNode with terminal marker
└─ return TraceResult(nodes, edges, terminals, truncated)
```

## Dependencies

**Imports:**
- `datetime, timezone` — timestamp handling
- `.terminals`, `.cross_chain`, `.mixer_exit` — local modules
- Async data layer (TODO: `backend.data.graph.queries`, `backend.data.providers.fallback`)
- Async label resolver (TODO: `backend.core.labeler.merge`)

**Imported by:**
- `backend.workers.trace_job` — RQ wrapper
- `backend.api.routes.trace` — HTTP endpoint

## Extension Points

1. **Fan-out control:** Adjust `DEFAULT_FANOUT` or make it a parameter to `trace()`.
2. **Terminal classifiers:** Add new types in `terminals.py` (e.g., staking, liquidity pool).
3. **Mixer exit scoring:** Tune weights `W_TIMING`, `W_GAS`, `W_BEHAVIOR` in `mixer_exit.py`.
4. **Cross-chain bridge list:** Extend `BRIDGE_CONTRACTS` in `terminals.py` or use dynamic registry.

## Testing Guidance

**Unit tests:** Mock `_get_outflows()` and `_resolve_labels()` with test transaction sets. Verify:
- Frontier expansion respects max_hops and MAX_WALLETS limits
- Terminal classification is correct for hardcoded addresses
- Fan-out produces exactly `fanout` top edges + rest in `additional_outflows`
- Truncation flag set when wallet limit hit

**Integration tests:** Run against testnet (e.g., Sepolia) with known addresses. Verify:
- Bridge matching tolerates ±0.5% value and ±30min timestamp
- Tornado exit candidates ranked correctly by composite score
- All candidates marked `unconfirmed=True`

## Known Gaps & TODOs

- `engine.py:77` — `_get_outflows()` stubbed; awaits Neo4j + provider wiring
- `engine.py:89` — `_resolve_labels()` stubbed; awaits labeler.merge wiring
- `cross_chain.py:32` — `match_bridge_out()` stubbed; awaits provider wiring
- `mixer_exit.py:83` — `match_tornado_exits()` stubbed; awaits provider wiring
- `mixer_exit.py:113` — recipient behavior fetch stubbed; awaits graph wiring
- No Solana support in bridge matching (todo in CLAUDE.md §17)
- No multi-sig wallet detection heuristic

## See Also

- `profiler.md` — uses tracer output for counterparty analysis
- `labeler.md` — supplies terminal classification labels
- `data-providers.md` — wires outflow data sources
- `data-graph.md` — Neo4j storage for upsert pattern
