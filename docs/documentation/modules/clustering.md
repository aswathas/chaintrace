# Clustering Module

**Location:** `backend/core/clustering/`

## Purpose

Detect related wallets via four heuristics: common funder, behavioral fingerprint, nonce-linked contracts, and co-spend patterns. Merge results via union-find. Return wallet clusters with per-edge heuristic evidence and confidence scores.

## Public API

### `merger.py` (entry point)

**`cluster_wallets(wallets: list[dict], wallet_txs: Optional[dict] = None, deployed_contracts: Optional[list] = None, funding_edges: Optional[list] = None, multi_party_txs: Optional[list] = None, min_confidence: float = 0.6) -> ClusterResult`**
Run all four heuristics; merge via union-find; return clusters above confidence threshold.

**`ClusterResult`** (dataclass)
```python
clusters: list[Cluster]         # groups of ≥2 wallets
all_edges: list[ClusterEdge]    # edges above min_confidence
dropped_edges: list[ClusterEdge] # edges below threshold
```

**`Cluster`** (dataclass)
```python
id: str                         # root wallet address
members: list[str]              # sorted member addresses
edges: list[ClusterEdge]        # edges within this cluster
heuristics: list[str]           # ["common_funder", "fingerprint", ...]
min_confidence: float
max_confidence: float
```

**`ClusterEdge`** (dataclass)
```python
wallet_a: str
wallet_b: str
heuristic: str                  # which heuristic found this link
confidence: float               # 0.0–1.0
evidence: str                   # human-readable explanation
```

### `common_funder.py`

**`find_common_funder_clusters(wallets: list[dict]) -> list[ClusterEdge]`**
Wallets funded by same address within 7-day window. Confidence higher when funded very close together (exponential decay).

**Requires:** `wallet.first_funder`, `wallet.first_funded_at` (unix timestamp).

**Confidence formula:** `max(0.6, 1.0 - (delta_hours / 168))`

### `fingerprint.py`

**`find_fingerprint_clusters(wallet_txs: dict[str, list[dict]]) -> list[ClusterEdge]`**
Behavioral fingerprinting: same gas price pattern + similar tx-timing histogram. Uses cosine similarity on histogram features.

**Requires:** `wallet_txs: {address: [tx dict]}` with gas_price_gwei and timestamp fields.

**Cosine similarity threshold:** likely ~0.8+ for high confidence.

### `nonce_linked.py`

**`find_nonce_linked_clusters(deployed_contracts: list[dict], funding_edges: list[dict]) -> list[ClusterEdge]`**
Contract deployer + wallet that funded the deployer = likely same entity.

**Requires:**
- `deployed_contracts: [{deployer: str, contract_address: str}]`
- `funding_edges: [{from: str, to: str, tx_hash: str}]`

**Confidence:** usually 0.85–0.95 (strong signal).

### `co_spend.py`

**`find_co_spend_clusters(multi_party_txs: list[dict]) -> list[ClusterEdge]`**
Wallets that appear together as inputs/recipients in ≥3 txs. Likely coordinated or sybil cluster.

**Requires:** `multi_party_txs: [{participants: [str], tx_hash: str}]`

**Confidence:** `min(1.0, 0.5 + (co_spend_count / 10))` — stronger with more co-spends.

## Algorithm & Data Flow

```
cluster_wallets(wallets, wallet_txs, deployed_contracts, funding_edges, multi_party_txs, min_confidence=0.6)
├─ Heuristic 1: find_common_funder_clusters(wallets)
├─ Heuristic 2: find_fingerprint_clusters(wallet_txs) [if wallet_txs provided]
├─ Heuristic 3: find_nonce_linked_clusters(...) [if both provided]
├─ Heuristic 4: find_co_spend_clusters(...) [if provided]
├─ Merge all edges; filter by min_confidence
├─ Union-find:
│  ├─ for each edge: uf.union(wallet_a, wallet_b)
│  └─ groups = uf.groups() → {root: [members]} for groups ≥ size 2
├─ Build Cluster objects with per-cluster edges and heuristics
└─ return ClusterResult(clusters, all_edges, dropped_edges)

Union-Find (path-compressed):
├─ find(x) → root with path compression
└─ union(x, y) → merge by rank
```

## Dependencies

**Imports:**
- `.common_funder`, `.fingerprint`, `.nonce_linked`, `.co_spend` — four heuristics

**Imported by:**
- `backend.api.routes.cluster` — HTTP POST `/cluster`
- UI clustering overlay layer

## Extension Points

1. **Add new heuristic:** Implement `find_*_clusters()` returning `list[ClusterEdge]`, call in `cluster_wallets()`.
2. **Adjust confidence thresholds:** Change `MIN_CONFIDENCE` constant or parameterize per heuristic.
3. **Tune individual heuristic scores:** Adjust confidence formulas in each heuristic module.
4. **Visualization params:** Use `cluster.min_confidence` / `cluster.max_confidence` to set edge opacity in UI.

## Testing Guidance

**Unit tests:**
- Create test wallets with known funding relationships; verify `find_common_funder_clusters()` links them
- Create tx sets with matching gas prices + timing; verify `find_fingerprint_clusters()` detects them
- Create deployed contracts + funding edges; verify `find_nonce_linked_clusters()` links deployer + funder
- Create multi-party txs; verify `find_co_spend_clusters()` detects co-spenders
- Verify union-find merges transitive edges (A-B, B-C → cluster {A, B, C})
- Verify `min_confidence` filtering drops low-confidence edges

**Integration:**
- Create synthetic cluster of 5 wallets linked by multiple heuristics
- Verify final cluster contains all 5 members
- Verify `cluster.heuristics` lists all applicable heuristic types
- Verify confidence ranges make sense (0.6–1.0 for most clusters)

## Known Gaps & TODOs

No explicit TODOs in merger.py. Implicit assumptions:
- All wallet dicts have `.address` field
- Timestamps are unix seconds
- Gas prices in gwei
- Union-find implementation is correct (path-compressed)

**Potential improvements:**
- Temporal filtering (only link wallets active in same period)
- Chain-specific clustering (don't link wallets on different chains without bridge evidence)
- Exclusion list (known legitimate multi-wallet patterns: exchange cold storage, protocol treasury)

## See Also

- `tracer.md` — may benefit from cluster info (skip investigating all cluster members if one is known terminal)
- `profiler.md` — can aggregate risk scores across cluster
