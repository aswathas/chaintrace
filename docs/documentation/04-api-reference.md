# API Reference

This document covers every endpoint in the ChainTrace FastAPI backend. All routes are prefixed with `/api/v1`. Long-running endpoints return a `job_id` and support WebSocket streaming for live updates.

Base URL (local): `http://localhost:8000/api/v1`

---

## Health

### `GET /health`

Reports connectivity status for all services and the current provider key pool. This endpoint is unauthenticated and safe to use as a load-balancer health check.

**Response — healthy:**

```json
{
  "status": "ok",
  "redis": true,
  "neo4j": true,
  "provider_pool": {
    "etherscan_keys": 5,
    "covalent": true,
    "alchemy": true
  }
}
```

**Response — degraded** (e.g., Neo4j unreachable):

```json
{
  "status": "degraded",
  "redis": true,
  "neo4j": false,
  "provider_pool": {
    "etherscan_keys": 3,
    "covalent": true,
    "alchemy": false
  }
}
```

---

## Trace

### `POST /trace`

Enqueue a hack-trace job starting from a seed wallet or transaction hash. Returns immediately with a `job_id`. The actual traversal runs in an RQ worker.

**Request body:**

```json
{
  "seed": "0x098B716B8Aaf21512996dC57EB0615e2383E2f96",
  "chain": "eth",
  "max_hops": 10,
  "min_value_usd": 100
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `seed` | string | yes | Starting wallet address or transaction hash |
| `chain` | string | yes | Chain identifier — see supported chains below |
| `max_hops` | integer | no | Maximum traversal depth (default: 10, max: 20) |
| `min_value_usd` | number | no | Skip outflows below this USD value (default: 100) |

**Supported chain values:** `eth`, `polygon`, `arbitrum`, `base`, `bnb`, `solana`

**Response (HTTP 202):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

**curl example:**

```bash
curl -X POST http://localhost:8000/api/v1/trace \
  -H "Content-Type: application/json" \
  -d '{"seed": "0x098B716B8Aaf21512996dC57EB0615e2383E2f96", "chain": "eth", "max_hops": 5}'
```

**Enqueued worker:** `workers.trace_job.run_trace` — timeout 600 seconds.

---

### `GET /trace/{job_id}`

Fetch the result of a completed trace job, or the current status if still running.

**Response — running:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started"
}
```

**Response — complete:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "complete",
  "seed": "0x098B716B8Aaf21512996dC57EB0615e2383E2f96",
  "chain": "eth",
  "hops_explored": 47,
  "wallets_visited": 23,
  "terminals": [
    {
      "address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
      "type": "mixer",
      "label": "Tornado Cash: 100 ETH Pool",
      "value_usd": 4200000,
      "tx_hash": "0xabc123...",
      "block": 14932105,
      "timestamp": "2022-04-03T10:22:11Z",
      "confirmed": false
    },
    {
      "address": "0xA7efAE728D2936e78BDA97dc267687568dD593f3",
      "type": "cex_deposit",
      "label": "Binance Hot Wallet 7",
      "value_usd": 12000000,
      "tx_hash": "0xdef456...",
      "block": 14940000,
      "timestamp": "2022-04-03T14:05:00Z",
      "confirmed": true
    }
  ],
  "nodes": [...],
  "edges": [...],
  "stale": false
}
```

**Response — not found (HTTP 404):**

```json
{
  "detail": "Job not found"
}
```

---

### `WebSocket /trace/{job_id}/stream`

Stream live hop updates as the trace worker publishes them. Connect immediately after `POST /trace` — the server will begin sending frames as each wallet layer is processed.

**Connection:**

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/trace/550e8400.../stream");
ws.onmessage = (event) => {
  const hop = JSON.parse(event.data);
  console.log(hop);
};
```

**Frame shape — hop discovered:**

```json
{
  "type": "hop",
  "depth": 2,
  "from": "0x098B716B8Aaf21512996dC57EB0615e2383E2f96",
  "to": "0xb3764761E297D6f121e79C32A65829Cd1dDb4D32",
  "tx_hash": "0x...",
  "value_eth": "3200.0",
  "value_usd": 6400000,
  "timestamp": "2022-04-03T09:45:22Z"
}
```

**Frame shape — terminal reached:**

```json
{
  "type": "terminal",
  "address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
  "terminal_type": "mixer",
  "label": "Tornado Cash: 100 ETH Pool",
  "value_usd": 4200000
}
```

**Frame shape — trace complete:**

```json
{
  "type": "complete",
  "wallets_visited": 23,
  "terminals_found": 2
}
```

The server closes the WebSocket after publishing the `complete` frame.

---

## Profile

### `POST /profile`

Enqueue a wallet profile job. Returns immediately with a `job_id`. The job fetches transaction history, computes risk score, resolves labels, and maps counterparties.

**Request body:**

```json
{
  "address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
  "chain": "eth"
}
```

**Response (HTTP 202):**

```json
{
  "job_id": "7f3c9a12-...",
  "status": "queued"
}
```

**Enqueued worker:** `workers.profile_job.run_profile` — timeout 300 seconds.

---

### `GET /profile/{address}?chain=eth`

Return a cached wallet profile. Returns HTTP 404 if the address has not been profiled yet — submit via `POST /profile` first.

**Query parameters:**

| Parameter | Default | Description |
|---|---|---|
| `chain` | `eth` | Chain to look up the profile for |

**Response:**

```json
{
  "address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
  "chain": "eth",
  "risk_score": 82,
  "risk_band": "critical",
  "labels": [
    {
      "label": "Tornado Cash: 100 ETH Pool",
      "source": "hardcoded",
      "confidence": 1.0
    }
  ],
  "tx_count": 14729,
  "balance_eth": "0.0",
  "balance_usd": 0,
  "first_seen": "2019-12-20T00:00:00Z",
  "last_seen": "2023-08-01T12:00:00Z",
  "is_contract": true,
  "counterparties": {
    "top_senders": [
      {"address": "0x...", "label": "Unknown", "value_usd": 100000, "tx_count": 1}
    ],
    "top_receivers": []
  },
  "behavior": {
    "high_velocity_small_tx": false,
    "round_amount_transfers": false,
    "recently_created": false
  },
  "scoring_breakdown": {
    "mixer_interaction": 40,
    "darknet_counterparty": 0,
    "exploit_wallet_interaction": 30,
    "high_velocity_small_tx": 0,
    "round_amount_transfers": 0,
    "recently_created": 0,
    "verified_protocol": -10,
    "cex_counterparty": -5
  }
}
```

---

## Cluster

### `POST /cluster`

Enqueue an entity clustering job around a seed wallet. The job runs all four heuristics (common funder, behavioral fingerprint, nonce-linked, co-spend) and returns the cluster graph.

**Request body:**

```json
{
  "address": "0x098B716B8Aaf21512996dC57EB0615e2383E2f96",
  "chain": "eth"
}
```

**Response (HTTP 202):**

```json
{
  "job_id": "9a1b2c3d-...",
  "status": "queued"
}
```

**Enqueued worker:** `workers.cluster_job.run_cluster` — timeout 300 seconds.

Fetch the result via `GET /trace/{job_id}` (cluster results share the same result-fetch pattern and are stored in the same Redis key namespace by job_id).

---

## Monitor

### `POST /monitor`

Register a wallet alert rule. Rules are stored in Redis and evaluated against inbound webhook events.

**Request body:**

```json
{
  "address": "0x098B716B8Aaf21512996dC57EB0615e2383E2f96",
  "chain": "eth",
  "min_value_usd": 10000,
  "label_filter": "mixer",
  "notify": ["discord", "telegram"]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `address` | string | yes | Wallet to monitor |
| `chain` | string | yes | Chain to monitor |
| `min_value_usd` | number | no | Only alert if transaction value exceeds this threshold |
| `label_filter` | string | no | Only alert if counterparty label matches (e.g., `"mixer"`, `"darknet"`) |
| `notify` | array | no | Notification channels: `"discord"`, `"telegram"` |

**Response (HTTP 201):**

```json
{
  "rule_id": "b5d9e1a0-..."
}
```

---

### `GET /monitor/alerts`

Return all triggered alert events.

**Response:**

```json
[
  {
    "rule_id": "b5d9e1a0-...",
    "address": "0x098B716B8Aaf21512996dC57EB0615e2383E2f96",
    "chain": "eth",
    "tx_hash": "0xfed321...",
    "value_usd": 450000,
    "counterparty": "0xabc...",
    "counterparty_label": "Tornado Cash: 10 ETH Pool",
    "triggered_at": "2026-04-24T09:00:00Z"
  }
]
```

---

### `POST /monitor/hook`

Ingest an inbound Alchemy or Moralis webhook payload. This endpoint is called by the webhook provider — not by users directly. It enqueues a job that evaluates the payload against all registered alert rules.

**Request body:** Raw JSON payload from Alchemy or Moralis (format varies by provider — the worker normalizes both formats).

**Response:**

```json
{
  "job_id": "c3d4e5f6-...",
  "received": true
}
```

**Enqueued worker:** `workers.monitor_job.process_webhook` — timeout 60 seconds.

---

## Report

### `POST /report/{job_id}?kind=trace`

Generate an AI-formatted prose report for a completed trace or profile job. The report text is generated by the configured AI provider (Groq or Ollama) using pre-analyzed JSON as context.

**Path parameters:**

| Parameter | Description |
|---|---|
| `job_id` | Job ID of a completed trace or profile job |

**Query parameters:**

| Parameter | Default | Description |
|---|---|---|
| `kind` | `trace` | Report type: `trace` or `profile` |

**Response:**

```json
{
  "job_id": "550e8400-...",
  "kind": "trace",
  "report": "On April 3, 2022, an attacker drained approximately $622M from the Ronin Bridge by exploiting compromised validator keys. Funds were initially consolidated at 0x098B... before being routed through three intermediate wallets over 12 hours. The largest outflow — $412M in ETH — reached Tornado Cash's 100 ETH pool within 48 hours of the exploit. A secondary outflow of $24M was deposited directly into a Binance hot wallet at block 14,940,000; the corresponding deposit hash and timestamp have been preserved for law enforcement referral. The remaining $186M has not yet been linked to a terminal destination as of the last trace run."
}
```

**Error — job not found (HTTP 404):**

```json
{
  "detail": "No result found for job_id"
}
```

**Error — AI unavailable (HTTP 503):**

```json
{
  "detail": "AI module not yet available"
}
```

---

## Labels

### `GET /labels/{address}`

Return the merged label for an address from the Redis cache. The label is populated lazily — when the address is first resolved during a trace or profile job.

**Response:**

```json
{
  "address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
  "label": "Tornado Cash: 100 ETH Pool",
  "source": "hardcoded",
  "confidence": 1.0,
  "tags": ["mixer", "sanctioned"],
  "chain": "eth"
}
```

**Error — no label (HTTP 404):**

```json
{
  "detail": "No label found for address"
}
```

---

### `POST /labels`

Submit a community label for an address. Submissions are cached in Redis pending review before promotion to the community label source.

**Request body:**

```json
{
  "address": "0xA7efAE728D2936e78BDA97dc267687568dD593f3",
  "chain": "eth",
  "label": "Binance Hot Wallet 7",
  "tags": ["cex", "binance"],
  "confidence": 0.9,
  "notes": "Consistent with Binance deposit patterns; cross-referenced with Etherscan public tag"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `address` | string | yes | Address being labeled |
| `chain` | string | yes | Chain the label applies to |
| `label` | string | yes | Human-readable label |
| `tags` | array | no | Machine-readable tags (e.g., `"cex"`, `"mixer"`, `"bridge"`) |
| `confidence` | number | no | Submitter's confidence 0–1 (default: 0.5) |
| `notes` | string | no | Supporting evidence or rationale |

**Response (HTTP 201):**

```json
{
  "address": "0xA7efAE728D2936e78BDA97dc267687568dD593f3",
  "status": "submitted"
}
```

---

## Error responses

All endpoints use standard FastAPI error format:

```json
{
  "detail": "Human-readable error message"
}
```

| HTTP status | Meaning |
|---|---|
| 202 | Job accepted and queued |
| 201 | Resource created |
| 404 | Job not found, profile not cached, or no label for address |
| 422 | Request body validation failed (Pydantic) |
| 503 | Required service (AI module) not available |

---

## Pydantic schemas reference

### `TraceRequest`

```python
class TraceRequest(BaseModel):
    seed: str                    # wallet address or tx hash
    chain: ChainEnum             # eth | polygon | arbitrum | base | bnb | solana
    max_hops: int = 10
    min_value_usd: float = 100.0
```

### `Address`

Used by `POST /profile` and `POST /cluster`:

```python
class Address(BaseModel):
    address: str
    chain: ChainEnum = ChainEnum.eth
```

### `AlertRule`

```python
class AlertRule(BaseModel):
    rule_id: Optional[str] = None       # assigned server-side if omitted
    address: str
    chain: ChainEnum
    min_value_usd: Optional[float] = None
    label_filter: Optional[str] = None
    notify: List[str] = []              # ["discord", "telegram"]
```

### `Label`

```python
class Label(BaseModel):
    address: str
    chain: str
    label: str
    source: Optional[LabelSource] = None   # assigned server-side
    tags: List[str] = []
    confidence: float = 0.5
    notes: Optional[str] = None
    created_at: Optional[datetime] = None  # assigned server-side
```

### `LabelSource` (enum)

```python
class LabelSource(str, Enum):
    hardcoded   = "hardcoded"
    community   = "community"
    etherscan   = "etherscan"
    arkham      = "arkham"
    submission  = "submission"
    heuristic   = "heuristic"
```

---

## See also

- [05-data-model.md](05-data-model.md) — the Neo4j and Redis structures behind these responses
- [09-operations.md](09-operations.md) — diagnosing slow or failing API calls
- [02-getting-started.md](02-getting-started.md) — curl examples against a running instance
