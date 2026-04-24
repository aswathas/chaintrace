# Data Model

This document describes how ChainTrace stores data across its three persistence layers: Neo4j (graph of wallets and transactions), PostgreSQL (relational metadata), and Redis (cache and queue). It also explains how data moves between the three.

---

## Neo4j — graph schema

Neo4j stores the core forensic graph: wallets, transactions between them, cluster relationships, and incident linkages. The graph grows with every investigation and is the primary cache for re-investigations.

### Node: `Wallet`

Represents any on-chain address — EOA, contract, or exchange.

```cypher
(:Wallet {
  address:         String,   // checksummed hex address or base58 (Solana)
  chain:           String,   // "eth" | "polygon" | "arbitrum" | "base" | "bnb" | "solana"
  first_seen:      DateTime, // block timestamp of first observed transaction
  last_seen:       DateTime, // block timestamp of most recent observed transaction
  tx_count:        Integer,
  balance_usd:     Float,    // snapshot at last profile time
  labels:          [String], // merged label tags e.g. ["mixer", "tornado_cash"]
  risk_score:      Integer,  // 0–100
  is_contract:     Boolean,
  created_at_block: Integer  // null for pre-existing wallets
})
```

**Example query — fetch a wallet and its labels:**

```cypher
MATCH (w:Wallet {address: "0x098B716B8Aaf21512996dC57EB0615e2383E2f96", chain: "eth"})
RETURN w.risk_score, w.labels, w.tx_count
```

---

### Node: `Contract`

A smart contract address, separate from `Wallet` for protocol interaction tracking.

```cypher
(:Contract {
  address:    String,
  chain:      String,
  name:       String,   // "Tornado Cash 100 ETH", "Uniswap V3 Router"
  protocol:   String,   // "tornado_cash" | "uniswap" | "aave" | "wormhole"
  abi_hash:   String    // keccak256 of ABI for verification
})
```

---

### Node: `Transaction`

Represents a single on-chain transaction (not a transfer — the edge `SENT` carries the transfer data).

```cypher
(:Transaction {
  hash:      String,
  block:     Integer,
  chain:     String,
  timestamp: DateTime,
  method:    String,    // decoded function name e.g. "deposit", "transfer"
  decoded:   Boolean    // true if ABI decoding succeeded
})
```

---

### Node: `Incident`

A named exploit or theft event. Pre-seeded for major hacks; auto-linked when trace traversal encounters a known seed.

```cypher
(:Incident {
  id:               String,  // "ronin-2022", "harmony-2022", "nomad-2022"
  name:             String,  // "Ronin Bridge Hack"
  date:             Date,
  total_stolen_usd: Float,
  chains:           [String]
})
```

---

### Relationships

#### `SENT`

A value transfer from one wallet to another, optionally carrying a token.

```cypher
(:Wallet)-[:SENT {
  tx_hash:   String,
  block:     Integer,
  timestamp: DateTime,
  value:     Float,       // raw token units
  value_usd: Float,
  token:     String,      // "ETH" | "USDC" | "WBTC" etc.
  chain:     String
}]->(:Wallet)
```

**Example — trace outflows from a wallet sorted by value:**

```cypher
MATCH (w:Wallet {address: "0x098B716B8Aaf21512996dC57EB0615e2383E2f96"})-[s:SENT]->(dst:Wallet)
RETURN dst.address, s.value_usd, s.token, s.timestamp
ORDER BY s.value_usd DESC
LIMIT 10
```

#### `INTERACTED_WITH`

Tracks protocol interactions (DEX swaps, mixer deposits, bridge calls).

```cypher
(:Wallet)-[:INTERACTED_WITH {
  protocol: String,  // "tornado_cash" | "uniswap_v3" | "stargate"
  method:   String   // decoded method name
}]->(:Contract)
```

#### `CLUSTERED_WITH`

Links wallets that entity clustering has determined likely belong to the same actor.

```cypher
(:Wallet)-[:CLUSTERED_WITH {
  heuristic:  String,  // "common_funder" | "behavioral_fingerprint" | "nonce_linked" | "co_spend"
  confidence: Float,   // 0.0–1.0; only edges ≥ 0.6 are rendered by default
  detected_at: DateTime
}]->(:Wallet)
```

#### `PART_OF`

Links a transaction to an incident when the tx is part of a known hack trace.

```cypher
(:Transaction)-[:PART_OF]->(:Incident)
```

---

### Example Cypher queries

**Find all wallets two hops from a known exploit address:**

```cypher
MATCH p = (:Wallet {address: "0x098B716B8Aaf21512996dC57EB0615e2383E2f96"})-[:SENT*1..2]->(dst:Wallet)
RETURN dst.address, dst.risk_score, dst.labels
```

**Find the shortest path between two wallets:**

```cypher
MATCH p = shortestPath(
  (a:Wallet {address: "0x098B716..."})
  -[:SENT*]->
  (b:Wallet {address: "0xd90e2f92..."})
)
RETURN length(p), [n IN nodes(p) | n.address]
```

**Find all wallets in a cluster:**

```cypher
MATCH (w:Wallet {address: "0x098B716..."})-[:CLUSTERED_WITH*1..3]-(peer:Wallet)
WHERE ALL(r IN relationships(path) WHERE r.confidence >= 0.6)
RETURN DISTINCT peer.address, peer.risk_score
```

---

## PostgreSQL — relational schema

PostgreSQL holds structured metadata that benefits from relational queries, constraints, and foreign keys. The schema is managed via SQLAlchemy migrations.

### `community_labels`

Snapshot of labels ingested from community GitHub repos (`brianleect/etherscan-labels`, `dawsbot/eth-labels`). Refreshed by a weekly cron job.

```sql
CREATE TABLE community_labels (
    id            SERIAL PRIMARY KEY,
    address       TEXT NOT NULL,
    chain         TEXT NOT NULL DEFAULT 'eth',
    label         TEXT NOT NULL,
    tags          TEXT[],
    source_repo   TEXT,           -- "brianleect/etherscan-labels"
    ingested_at   TIMESTAMPTZ DEFAULT now(),
    UNIQUE (address, chain, source_repo)
);
CREATE INDEX ON community_labels (address, chain);
```

### `submitted_labels`

Community label submissions from users via `POST /labels`. Flagged for review before promotion.

```sql
CREATE TABLE submitted_labels (
    id            SERIAL PRIMARY KEY,
    address       TEXT NOT NULL,
    chain         TEXT NOT NULL,
    label         TEXT NOT NULL,
    tags          TEXT[],
    confidence    FLOAT DEFAULT 0.5,
    notes         TEXT,
    submitter_id  TEXT,           -- null for anonymous submissions
    status        TEXT DEFAULT 'pending',  -- pending | approved | rejected
    created_at    TIMESTAMPTZ DEFAULT now(),
    reviewed_at   TIMESTAMPTZ,
    reviewed_by   TEXT
);
CREATE INDEX ON submitted_labels (address, chain);
CREATE INDEX ON submitted_labels (status);
```

### `alert_rules`

Persistent alert rule storage. Redis holds the working copy; Postgres is the durable source of truth.

```sql
CREATE TABLE alert_rules (
    rule_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address         TEXT NOT NULL,
    chain           TEXT NOT NULL,
    min_value_usd   FLOAT,
    label_filter    TEXT,
    notify          TEXT[],         -- {"discord", "telegram"}
    enabled         BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON alert_rules (address, chain, enabled);
```

### `alert_events`

Record of every triggered alert for audit and display.

```sql
CREATE TABLE alert_events (
    id              SERIAL PRIMARY KEY,
    rule_id         UUID REFERENCES alert_rules(rule_id),
    tx_hash         TEXT,
    from_address    TEXT,
    to_address      TEXT,
    value_usd       FLOAT,
    chain           TEXT,
    triggered_at    TIMESTAMPTZ DEFAULT now(),
    notified        BOOLEAN DEFAULT false
);
```

### `risk_overrides`

Operator-set manual risk score overrides for specific addresses. Takes priority over computed scores.

```sql
CREATE TABLE risk_overrides (
    address         TEXT NOT NULL,
    chain           TEXT NOT NULL,
    risk_score      INTEGER CHECK (risk_score BETWEEN 0 AND 100),
    reason          TEXT,
    set_by          TEXT,
    set_at          TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (address, chain)
);
```

### `incidents`

Pre-seeded known exploit events that are mirrored into Neo4j `Incident` nodes.

```sql
CREATE TABLE incidents (
    id              TEXT PRIMARY KEY,   -- "ronin-2022"
    name            TEXT NOT NULL,
    date            DATE,
    total_stolen_usd FLOAT,
    chains          TEXT[],
    seed_addresses  TEXT[],             -- known attacker wallet addresses
    description     TEXT,
    source_url      TEXT
);
```

---

## Redis — key schema and TTL policy

Redis serves three roles: cache, RQ job queue, and WebSocket PubSub. Key naming is namespaced to avoid collisions.

### Cache keys

| Key pattern | TTL | Contents |
|---|---|---|
| `label:{address}` | 3600s (1h) | Merged label JSON for an address |
| `profile:{chain}:{address}` | 300s (5min) | Full wallet profile JSON |
| `trace:{job_id}` | 86400s (24h) | Complete trace result JSON |
| `tx:{chain}:{tx_hash}` | permanent | Single transaction data (blocks are immutable) |
| `wallet_txs:{chain}:{address}:{page}` | 300s or permanent | Transaction history page; permanent if all txs > 1000 blocks old |
| `balance:{chain}:{address}` | 30s | Current wallet balance |

**TTL strategy rationale:**
- Transactions older than 1,000 blocks are immutable → permanent cache. No re-fetch needed.
- Recent transaction history → 5-minute TTL to catch new incoming transactions.
- Balances → 30-second TTL (highly volatile).
- Labels → 1-hour TTL (community submissions need time to propagate).

### Queue keys

RQ uses Redis automatically. Key patterns managed by RQ internals:

| Key pattern | Purpose |
|---|---|
| `rq:queues` | Set of all queue names |
| `rq:queue:default` | Pending job IDs |
| `rq:job:{job_id}` | Serialized job state |
| `rq:workers` | Set of active worker keys |

### PubSub channels

| Channel | Publisher | Subscriber |
|---|---|---|
| `trace:stream:{job_id}` | `workers.trace_job` (one message per hop) | WebSocket handler at `/trace/{job_id}/stream` |
| `monitor:alerts` | `workers.monitor_job` | Frontend alert dashboard via WebSocket |

### Alert state keys

| Key | Contents |
|---|---|
| `monitor:rules` | JSON array of all registered `AlertRule` objects |
| `monitor:alerts` | JSON array of triggered alert events |

---

## Data flow across the three layers

```
POST /trace (new address)
  │
  ├── Worker: query Neo4j for existing wallet neighborhood
  │     hit: skip provider, use cached graph ──────────────────┐
  │     miss: call provider fallback chain                     │
  │            ├── fetch_txs(address)                          │
  │            ├── upsert (:Wallet) into Neo4j                 │
  │            └── upsert (:SENT) edges into Neo4j             │
  │                                                            │
  ├── labeler.merge.resolve(address)                           │
  │     1. hardcoded dict lookup                               │
  │     2. Redis GET label:{address}                           │
  │     3. Postgres SELECT community_labels                    │
  │     4. Etherscan API (cache result in Redis 1h)            │
  │     5. Arkham API (cache result in Redis 1h)               │
  │     6. Postgres SELECT submitted_labels WHERE status=approved│
  │     7. heuristic inference                                 │
  │     → Redis SET label:{address} (1h TTL)                  │
  │                                                            │
  ├── scorer.score(wallet_data)                                │
  │     → check Postgres risk_overrides first                  │
  │     → apply rule table                                     │
  │                                                            │
  └── RedisCache.set(trace:{job_id}, result, ttl=86400) <──────┘
       Redis PUBLISH trace:stream:{job_id} per hop
```

---

## See also

- [01-architecture.md](01-architecture.md) — why Neo4j serves as both DB and cache
- [04-api-reference.md](04-api-reference.md) — the response shapes that these models back
- [06-deployment.md](06-deployment.md) — backup strategy for Neo4j and Postgres data
