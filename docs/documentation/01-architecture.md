# Architecture

This document covers the full system architecture of ChainTrace: component responsibilities, data flow from user request to response, the rationale behind key technology choices, and deployment topology.

---

## Component diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│  Browser / API Client                                                │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTP/REST  WebSocket (monitor)
┌────────────────────────────▼─────────────────────────────────────────┐
│  Next.js 14 Frontend  (port 3000)                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐ │
│  │ /trace/[id]  │  │/profile/[a]  │  │ /monitor   │  │/report/[id]│ │
│  │ Cytoscape.js │  │ Risk card    │  │ Alert rules│  │ MD viewer  │ │
│  └──────────────┘  └──────────────┘  └────────────┘  └────────────┘ │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTP  /api/v1/*
┌────────────────────────────▼─────────────────────────────────────────┐
│  FastAPI Backend  (port 8000)                                        │
│  RequestLoggingMiddleware  ·  CORSMiddleware  ·  RateLimitMiddleware │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ /trace   │ │ /profile │ │ /cluster │ │ /monitor │ │ /report  │  │
│  │          │ │          │ │          │ │ /hook    │ │ /labels  │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       └────────────┴────────────┴─────────────┴─────────────┘        │
│                              │ enqueue                               │
│                    ┌─────────▼──────────┐                            │
│                    │    RQ Workers       │                            │
│                    │  trace_job.py       │                            │
│                    │  profile_job.py     │                            │
│                    │  monitor_job.py     │                            │
│                    └─────────┬──────────┘                            │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                     │
┌─────────▼────────┐  ┌────────▼───────┐  ┌────────▼────────┐
│  Neo4j 5         │  │  Redis 7       │  │  PostgreSQL 16  │
│  Community       │  │                │  │                 │
│  (port 7687)     │  │  Cache layer   │  │  Labels,        │
│  (port 7474 UI)  │  │  RQ job queue  │  │  alert configs, │
│  Wallet/Tx graph │  │  PubSub stream │  │  risk overrides │
└─────────┬────────┘  └────────────────┘  └─────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────────┐
│  Data Ingestion Layer                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Covalent │  │ Alchemy  │  │ Etherscan     │  │ The Graph      │  │
│  │ 100+     │  │ ETH/POL/ │  │ family        │  │ Uniswap/Aave/ │  │
│  │ chains   │  │ ARB/SOL  │  │ key pool      │  │ Curve/bridges  │  │
│  └──────────┘  └──────────┘  └──────────────┘  └────────────────┘  │
│  └──────────────────────────┴───────────────────── Public RPC fallback│
└──────────────────────────────────────────────────────────────────────┘
          │
┌─────────▼────────┐
│  AI Layer        │
│  Groq API        │  (primary — Llama 3.3 70B, free tier)
│  Ollama local    │  (fallback — gemma3:4b / phi4-mini / qwen2.5:3b)
└──────────────────┘
```

---

## Data flow: user request to response

### Synchronous path (label lookup, cached profile)

```
Client → GET /api/v1/labels/{address}
  → FastAPI route handler
  → RedisCache.get(label:{address})
  → hit → return JSON
  → miss → HTTP 404
```

### Async path (new trace or profile)

```
Client → POST /api/v1/trace
  → FastAPI handler → RQ.enqueue("workers.trace_job.run_trace", ...)
  → returns {job_id, status: "queued"}  (HTTP 202)

RQ Worker (separate process):
  → trace_job.run_trace(request)
  → provider_fallback.fetch_txs(seed_wallet)
      → try Covalent → 429? rotate key → pool cold? → try Alchemy → ...
  → tracer.engine.trace(seed, max_hops)
      → Neo4j query first (cache hit: zero provider calls)
      → miss → provider fetch → upsert into Neo4j
      → classify terminals (CEX / mixer / bridge / cold storage)
      → cross-chain bridge matching
  → profiler.scorer.score(wallet_data)
  → labeler.merge.resolve(address)
  → RedisCache.set(trace:{job_id}, result)
  → Redis PUBLISH trace:stream:{job_id} each hop update

Client → GET /api/v1/trace/{job_id}
  → Redis hit → return full result
  → Redis miss + RQ status → return {status: "running"}

Client → WS /api/v1/trace/{job_id}/stream
  → FastAPI WebSocket handler
  → Redis SUBSCRIBE trace:stream:{job_id}
  → forward each published hop message to client frame
```

### Report generation

```
Client → POST /api/v1/report/{job_id}?kind=trace
  → RedisCache.get(trace:{job_id}) → structured JSON context
  → ai.generate_report(kind, context)
      → AIProvider.generate(prompt_template, json_context)
      → post-check: every number/address in output must exist in context
      → fail → regenerate once → fail again → templated fallback
  → return {job_id, kind, report: "...prose..."}
```

---

## Why Neo4j as both database and cache

Neo4j is the persistence backbone, not just a graph query engine. Every wallet neighborhood fetched from external APIs is upserted into Neo4j immediately (`data/graph/upsert.py` uses idempotent MERGE statements). The consequence: a repeat investigation of any previously-seen address requires zero external API calls — the provider layer checks Neo4j first.

This makes ChainTrace dramatically more efficient at scale. The first investigation of a major exploit wallet is slow (multiple provider calls). Every subsequent investigation that touches any of those same wallets is instant. The graph grows smarter with every use.

The alternative — using Redis as a pure cache — would require TTL-based eviction and lose the graph traversal primitives (variable-length path queries, shortest path, community detection) that make the tracer possible.

---

## Why the provider fallback chain

No single free-tier API covers all chains, all transaction types, and all rate limits simultaneously. The fallback chain `Covalent → Alchemy → Etherscan family → Public RPC` gives ChainTrace resilience without paid subscriptions:

- **Covalent (GoldRush):** Unified API across 100+ chains. Best for cross-chain coverage.
- **Alchemy:** High reliability for Ethereum mainnet, Polygon, Arbitrum, Solana. Better rate limits on the free tier for heavy workloads.
- **Etherscan family:** Per-chain explorers with fine-grained transaction data. Key rotation across 5 keys = 25 req/sec free per chain.
- **The Graph:** All DeFi protocol data (Uniswap, Aave, Curve, bridges) at no cost, no rate limits.
- **Public RPC:** Last resort. Sufficient for balance queries and block lookups, unreliable for historical data.

On HTTP 429, the rotator marks the current key as cooling (60-second backoff) and tries the next key in the pool. When the pool is fully cooled, it escalates to the next provider. If all providers are exhausted, the system returns cached-only results with `stale: true` in the response.

---

## Why AI is a formatter, not an analyst

All intelligence in ChainTrace is deterministic Python:
- Graph traversal is BFS/DFS with fan-out caps
- Risk scoring is a weighted rule table clamped to [0, 100]
- Label resolution is a priority-ordered pipeline with first-hit semantics
- Cluster detection is four independent heuristics merged by union-find

The LLM receives the already-analyzed JSON (addresses, amounts, labels, scores, heuristic outputs) and writes human-readable prose. It does not make decisions. This design has three advantages:

1. **Reproducibility.** The same JSON input always produces the same forensic conclusion regardless of which AI model or version is running.
2. **Offline capability.** A gemma3:4b model running in Ollama locally produces acceptable prose. You do not need cloud access for core functionality.
3. **Auditability.** Every claim in an AI report can be traced back to the structured JSON context that was handed to the LLM. A post-generation regex check enforces this — if the LLM invents an address or amount not present in the context, the report is discarded and regenerated.

---

## Deployment topology

### Single-node (VPS / developer laptop)

```
┌──────────────────────────────────────────────────────┐
│  VPS or local machine                                │
│                                                      │
│  docker-compose up                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ neo4j    │  │ redis    │  │ postgres          │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ backend  │  │ rq worker│  │ frontend          │   │
│  │ :8000    │  │(same img)│  │ :3000             │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│  ┌──────────┐                                        │
│  │ ollama   │  (optional, --profile ollama)          │
│  │ :11434   │                                        │
│  └──────────┘                                        │
│                                                      │
│  Caddy / Traefik reverse proxy  (:443)               │
│  → /api/* → backend:8000                            │
│  → /*     → frontend:3000                           │
└──────────────────────────────────────────────────────┘
```

### What lives in each service

| Service | Image | Purpose | State |
|---|---|---|---|
| `neo4j` | `neo4j:5-community` | Graph DB — wallet/tx/cluster data | Persistent volume |
| `redis` | `redis:7-alpine` | Cache, RQ job queue, PubSub for WS | Ephemeral (cache) + optional AOF |
| `postgres` | `postgres:16-alpine` | Labels, alert rules, submitted labels | Persistent volume |
| `backend` | Built from `backend/Dockerfile` | FastAPI app + RQ worker | Stateless |
| `frontend` | Built from `frontend/Dockerfile` | Next.js SSR + static | Stateless |
| `ollama` | `ollama/ollama:latest` | Local AI inference | Model volume (optional) |

---

## See also

- [02-getting-started.md](02-getting-started.md) — run this architecture locally in 10 minutes
- [05-data-model.md](05-data-model.md) — what Neo4j, Postgres, and Redis actually store
- [06-deployment.md](06-deployment.md) — production deployment topology and hardening
- [Design specification](../superpowers/specs/chaintrace-design.md) — section 2 for architecture invariants
