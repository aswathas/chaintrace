# Data Graph Module

**Location:** `backend/data/graph/`

## Purpose

Neo4j client initialization and async query helpers. Persist wallet→tx→wallet relationships, contract interactions, and incident metadata. Enable fast neighborhood lookups and graph traversals.

## Public API

### `client.py`

**`async get_driver(uri: str, password: str, user: str = "neo4j") -> AsyncDriver`**
Singleton async Neo4j driver. Creates on first call; subsequent calls return cached instance. Logs connection info.

**`async close_driver() -> None`**
Close driver on shutdown. Called on app termination.

**Usage:**
```python
driver = await get_driver("bolt://localhost:7687", password="password")
async with driver.session() as session:
    result = await session.run("MATCH (n:Wallet) RETURN n LIMIT 5")
```

### `queries.py`

**Neo4j schema (from design spec):**

Nodes:
- `(:Wallet {address, chain, first_seen, last_seen, tx_count, balance_usd, labels[], risk_score, is_contract, created_at_block})`
- `(:Transaction {hash, block, chain, method, decoded})`
- `(:Contract {address, chain, standard, name})`
- `(:Incident {id, name, date, total_stolen_usd})`

Edges:
- `(:Wallet)-[:SENT {tx_hash, block, timestamp, value, token, value_usd, chain}]->(:Wallet)`
- `(:Wallet)-[:INTERACTED_WITH {protocol, method}]->(:Contract)`
- `(:Wallet)-[:CLUSTERED_WITH {heuristic, confidence}]->(:Wallet)`
- `(:Transaction)-[:PART_OF]->(:Incident)`

**Query helpers (likely in this file, may be stubbed):**
- `async get_outflows(address: str, chain: str) -> list[OutflowEdge]` — SENT edges from wallet
- `async get_inflows(address: str, chain: str) -> list[InflowEdge]` — incoming SENT edges
- `async get_wallet(address: str, chain: str) -> Optional[WalletNode]` — fetch wallet properties
- `async get_neighbors(address: str, depth: int = 1) -> list[str]` — all wallets within depth hops
- `async find_bridge_mint(bridge_label: str, token: str, min_value: float, max_value: float, min_ts: int, max_ts: int) -> Optional[dict]` — cross-chain bridge matching query

### `upsert.py`

**Idempotent upsert pattern:**

**`async upsert_wallet(address: str, chain: str, properties: dict) -> None`**
`CREATE OR UPDATE` wallet node. Merge properties.

**`async upsert_tx_edge(src: str, dst: str, tx_hash: str, properties: dict) -> None`**
Create SENT edge with idempotent key: `(src, dst, tx_hash)` — only one edge per tx.

**`async upsert_trace(trace_result: TraceResult, chain: str) -> None`**
Batch upsert all nodes + edges from a trace result. Idempotent — safe to re-run.

**Pattern (pseudo-Cypher):**
```cypher
MERGE (w:Wallet {address: $addr, chain: $chain})
ON CREATE SET w += $create_props
ON MATCH SET w += $update_props
WITH w
MERGE (w)-[e:SENT {tx_hash: $tx_hash}]->(dst:Wallet {address: $dst, chain: $chain})
SET e += $edge_props
```

## Algorithm & Data Flow

```
Initialization:
├─ FastAPI startup → await get_driver(NEO4J_URI, password)
└─ On shutdown → await close_driver()

Data persistence (from tracer):
├─ trace() returns TraceResult
├─ await upsert_trace(result, chain)
├─ upserts all HopNodes as Wallet nodes
├─ upserts all OutflowEdges as SENT relationships
└─ subsequent trace() calls find nodes in Neo4j-first

Neighborhood query (for profiler):
├─ await get_neighbors(address, depth=2)
├─ returns all wallets reachable within 2 hops
└─ used to populate counterparty graph

Bridge matching (for cross_chain):
├─ await find_bridge_mint(bridge_label, token, value_range, ts_range)
├─ queries Wallet nodes with bridge interaction + matching mint signature
└─ returns recipient address on destination chain
```

## Dependencies

**Imports:**
- `neo4j` — Neo4j driver (AsyncDriver, AsyncGraphDatabase)
- `structlog` — structured logging

**Imported by:**
- `backend.core.tracer.engine` — `_get_outflows()` (TODO)
- `backend.workers.trace_job` — `upsert_trace()` (TODO)
- `backend.api.routes.trace` — `get_neighbors()` for UI graph
- `backend.core.labeler.heuristic` — wallet behavior analysis

## Extension Points

1. **Add query:** Implement new async function in `queries.py` (e.g., `find_connected_components()` for clustering UI).
2. **Customize upsert properties:** Modify `upsert_wallet()` to handle custom fields (e.g., risk_score from profiler).
3. **Index optimization:** Add Cypher `CREATE INDEX` statements for frequently queried properties (address, chain, label).
4. **Relationship types:** Add new edge types (e.g., `:FUNDED_BY`, `:DEPLOYED`).

## Testing Guidance

**Unit tests:**
- Mock AsyncDriver; verify get_driver() singleton behavior
- Mock session; verify upsert queries generate correct Cypher
- Test idempotency: run upsert twice → same result

**Integration:**
- Spin up Neo4j Community in Docker
- Run upsert_trace() with known TraceResult
- Query MATCH (w:Wallet) RETURN w LIMIT 10 → verify nodes exist
- Run get_neighbors() → verify reachability
- Query MATCH (w)-[:SENT]->(w2) RETURN count(*) → verify edge count

## Known Gaps & TODOs

- `client.py:14` — Singleton pattern is module-level global; thread-safety not guaranteed in concurrent startup
- `queries.py` — File likely stubbed or incomplete; many query helpers not implemented
- `upsert.py` — Batch upsert pattern not optimized for large traces (consider UNWIND for bulk)
- No compound indexes (address + chain)
- No constraint on address uniqueness per chain
- No transaction boundaries in upsert; large batches may fail mid-stream
- No Neo4j version compatibility checks

## See Also

- `data-cache.md` — Redis cache layer sits above Neo4j
- `tracer.md` — primary consumer of graph queries (outflows, neighborhoods)
