# ChainTrace — Design Specification

**Status:** Draft v1
**Date:** 2026-04-24
**Owner:** aswathas20@gmail.com

---

## 1. Problem & Positioning

**Problem.** Blockchain forensics is dominated by closed, expensive SaaS (Chainalysis, TRM Labs, Elliptic). Security researchers, CTF players, small incident-response teams, and students have no open, self-hostable alternative that works across chains.

**Positioning.** ChainTrace is a free, self-hostable multi-chain forensics tool with two flagship modules:
- **Hack Tracer** — given a known exploit/theft tx or wallet, traverse fund flow hop-by-hop across chains until funds reach a terminal (CEX deposit, mixer, bridge, or cold storage).
- **Wallet Profiler** — given any address, produce a risk score (0–100), label, counterparty map, and behavioral summary.

**Non-goals.**
- Not a replacement for subpoena-backed investigation — no KYC data.
- Not a privacy-coin tool — Monero/Zcash-shielded are out of scope.
- Not real-time at Chainalysis scale — designed for single-investigation workloads, not dragnet surveillance.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Next.js 14 Frontend  ─  Cytoscape.js  ─  Tailwind           │
│  - Investigation UI   - Graph canvas  - Profile cards         │
│  - Alerts dashboard   - Report viewer - Cluster overlay       │
└────────────────────┬──────────────────┬──────────────────────┘
                     │ HTTP/REST        │ WebSocket (monitor)
┌────────────────────▼──────────────────▼──────────────────────┐
│                    FastAPI Backend (async)                    │
│   /trace  /profile  /cluster  /monitor  /report  /labels      │
└──┬───────────┬────────────┬───────────┬──────────────────────┘
   │           │            │           │
   ▼           ▼            ▼           ▼
┌──────┐  ┌────────┐  ┌──────────┐  ┌───────────┐
│Neo4j │  │ Redis  │  │PostgreSQL│  │ AI Layer  │
│graph │  │ cache  │  │ labels,  │  │ Groq /    │
│ DB   │  │ + RQ   │  │ metadata │  │ Ollama    │
└──────┘  └────────┘  └──────────┘  └───────────┘
   │
   ▼
┌──────────────────────────────────────────────────┐
│           Data Ingestion Layer                    │
│  Covalent → Alchemy → Etherscan fam → Public RPC  │
│  + The Graph (DeFi protocol data)                 │
└──────────────────────────────────────────────────┘
```

### 2.1 Architectural invariants

- **AI is a formatter, not an analyst.** Traversal, scoring, labeling, and clustering are deterministic Python. The LLM only consumes pre-analyzed JSON and writes prose. This makes the system reproducible and lets us use small local models.
- **Neo4j is both DB and cache.** Once a wallet's neighborhood is fetched, it is persisted. Repeat investigations of the same address = zero external API calls.
- **Everything flows through a provider abstraction.** No route handler talks to Covalent or Alchemy directly — they talk to the provider layer, which handles fallback, key rotation, and caching transparently.

---

## 3. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11+ / FastAPI | async I/O, typed, fast to iterate |
| Graph DB | Neo4j Community | native graph traversals; free self-host |
| Cache + queue | Redis + RQ | TTL cache + job queue in one process |
| Relational | PostgreSQL 16 | labels, risk overrides, alert configs |
| Frontend | Next.js 14 + TS + Tailwind | app router, server components for report rendering |
| Graph viz | Cytoscape.js | battle-tested, handles 10k+ nodes |
| AI primary | Groq API (Llama 3.3 70B) | free tier, fast, quality prose |
| AI fallback | Ollama (gemma3:4b / phi4-mini / qwen2.5:3b) | fully offline, privacy-respecting |
| Monitoring | Alchemy Webhooks + Moralis Streams | real-time wallet alerts |

---

## 4. Module Structure

```
backend/
  api/
    routes/            # trace.py, profile.py, cluster.py, monitor.py, report.py, labels.py
    deps.py            # shared FastAPI dependencies
    middleware.py      # request id, rate limit, auth
  core/
    tracer/            # hop-by-hop fund flow engine
      engine.py        # BFS/DFS traversal with terminal detection
      terminals.py     # CEX, mixer, bridge, cold-storage classifiers
      cross_chain.py   # bridge in/out matching
    profiler/          # risk score + summary
      scorer.py        # rule-based weighted scoring
      summary.py       # counterparty + behavior aggregation
    clustering/        # entity clustering heuristics
      common_funder.py
      fingerprint.py
      nonce_linked.py
      co_spend.py
    labeler/           # 5-source label pipeline
      hardcoded.py     # Tornado, bridges, DEX routers, CEX hot
      community.py     # brianleect/etherscan-labels, dawsbot/eth-labels
      etherscan.py     # public address tags
      arkham.py        # Arkham free API
      submissions.py   # user-contributed labels (Postgres)
      heuristic.py     # behavior-pattern → inferred label
      merge.py         # priority-ordered merge
    parser/            # ABI decoding + exploit pattern matching
      abi.py
      patterns.py      # reentrancy, flash-loan, approval-drain signatures
    monitor/           # real-time webhooks
      alchemy.py
      moralis.py
      dispatch.py      # Discord/Telegram notifiers
  data/
    providers/         # provider abstraction
      base.py          # Provider protocol (fetch_txs, fetch_balance, fetch_token_xfers)
      covalent.py
      alchemy.py
      etherscan.py     # + polygonscan, arbiscan, basescan, bscscan subclasses
      thegraph.py
      rpc.py           # public RPC fallback
      rotator.py       # key pool + 429-aware rotation
      fallback.py      # provider chain orchestrator
    cache/
      redis_cache.py   # TTL strategy: old tx = permanent, recent tx = 5min
      keys.py          # cache key schema
    graph/
      client.py        # neo4j driver
      queries.py       # cypher templates
      upsert.py        # idempotent wallet/tx upserts
  ai/
    providers/
      base.py          # AIProvider protocol (generate)
      groq.py
      ollama.py
      claude.py        # optional
      openai.py        # optional
    prompts/
      trace_report.py
      profile_summary.py
      cluster_explanation.py
  models/              # Pydantic
    wallet.py
    transaction.py
    trace.py
    profile.py
    cluster.py
    alert.py
  workers/             # RQ workers for long investigations
    trace_job.py
    profile_job.py
  main.py              # FastAPI entrypoint

frontend/
  app/
    (routes)/
      trace/[id]/       # investigation page
      profile/[addr]/   # wallet profile page
      monitor/          # alerts dashboard
      report/[id]/      # shareable report view
  components/
    graph/              # Cytoscape wrapper, legend, controls
    profiler/           # risk card, counterparty table, behavior chart
    tracer/             # hop timeline, terminal summary
    alerts/             # alert list, rule editor
    shared/             # address chip, chain badge, label pill
  lib/
    api.ts              # backend client
    ws.ts               # monitor WebSocket client
```

---

## 5. API Surface (v1)

All endpoints return JSON. Long-running endpoints return a `job_id` and stream updates via WebSocket.

| Method | Path | Purpose | Sync/Async |
|---|---|---|---|
| POST | `/trace` | Start hack trace from wallet or tx | Async (job) |
| GET | `/trace/{job_id}` | Fetch trace result | Sync |
| GET | `/trace/{job_id}/stream` | WebSocket — live hop updates | Stream |
| POST | `/profile` | Profile a wallet | Async (job) |
| GET | `/profile/{address}` | Fetch cached profile | Sync |
| POST | `/cluster` | Run clustering around a wallet | Async (job) |
| POST | `/monitor` | Register wallet alert rule | Sync |
| GET | `/monitor/alerts` | List triggered alerts | Sync |
| POST | `/report/{job_id}` | Generate AI-formatted report | Sync |
| GET | `/labels/{address}` | Resolve merged label | Sync |
| POST | `/labels` | Submit community label | Sync (authed) |

---

## 6. Data Model (Neo4j)

```
(:Wallet {
  address, chain, first_seen, last_seen,
  tx_count, balance_usd, labels[], risk_score,
  is_contract, created_at_block
})
  -[:SENT {tx_hash, block, timestamp, value, token, value_usd, chain}]->
(:Wallet)

(:Wallet)-[:INTERACTED_WITH {protocol, method}]->(:Contract)
(:Wallet)-[:CLUSTERED_WITH {heuristic, confidence}]->(:Wallet)

(:Transaction {hash, block, chain, method, decoded})
  -[:PART_OF]->(:Incident {id, name, date, total_stolen_usd})
```

**Postgres** holds: submitted labels, risk overrides, alert configs, user accounts (if auth enabled), incident metadata.

---

## 7. Core Algorithms

### 7.1 Hack Tracer (hop-by-hop traversal)

```
def trace(seed: Address, max_hops=10, min_value_usd=100):
    frontier = [(seed, 0, None)]        # (wallet, depth, parent_edge)
    visited  = set()
    terminals = []

    while frontier and len(visited) < MAX_WALLETS:
        w, depth, parent = frontier.pop(0)
        if w in visited or depth > max_hops: continue
        visited.add(w)

        outflows = get_outflows(w)                  # Neo4j-first, then providers
        outflows = filter_by_value(outflows, min_value_usd)
        outflows = follow_largest_n(outflows, n=5)  # fan-out control

        for edge in outflows:
            terminal = classify_terminal(edge.dst)  # CEX / mixer / bridge / cold
            if terminal:
                terminals.append((edge, terminal))
                if terminal == "bridge":
                    bridged = match_bridge_out(edge)  # cross-chain hop
                    if bridged: frontier.append((bridged, depth+1, edge))
            else:
                frontier.append((edge.dst, depth+1, edge))

    return build_trace_tree(seed, visited, terminals)
```

**Fan-out control.** Cap outflows-per-hop at 5 largest-by-value to prevent combinatorial explosion. Surface the rest as "additional outflows" in UI.

### 7.2 Wallet Profiler (risk score)

Rule-based weighted scoring, clamped to `[0, 100]`:

| Signal | Weight |
|---|---:|
| Direct mixer interaction (Tornado Cash, etc.) | +40 |
| Counterparty labeled darknet | +35 |
| Interacted with known exploit wallet | +30 |
| High-velocity small tx pattern | +15 |
| Round-amount transfers | +10 |
| Wallet age < 30 days | +5 |
| Verified protocol interaction | -10 |
| CEX-labeled counterparty | -5 |

Thresholds: `0-24 low · 25-49 medium · 50-74 high · 75+ critical`.

### 7.3 Mixer exit matching (Tornado Cash)

Tornado uses fixed denominations (0.1 / 1 / 10 / 100 ETH). On deposit:
1. Note denomination `D` and deposit block `B_dep`.
2. Scan all withdrawals of denomination `D` in window `[B_dep, B_dep + 72h]`.
3. Rank candidates by: timing proximity, gas-price fingerprint match, dest-wallet behavioral similarity.
4. Surface **all** candidates as probabilistic — clearly labeled "unconfirmed mixer exit".

### 7.4 Entity clustering

Four heuristics run independently; results merge via union-find:
1. **Common funder** — wallets first-funded from same source within 7-day window.
2. **Behavioral fingerprint** — same gas price pattern + tx-timing histogram.
3. **Nonce-linked** — deployer of a contract + the wallet that funded the deployer.
4. **Co-spend** — wallets that appear together as inputs/recipients in ≥3 txs.

Each cluster edge carries a `confidence` (0-1); we only render `≥ 0.6` by default.

---

## 8. Data Ingestion & Fallback

**Provider chain:** `Covalent → Alchemy → Etherscan-family → Public RPC`.

**Failure semantics:**
- HTTP 429 → mark key cooling for 60s, rotate to next key in pool.
- Full pool cold → escalate to next provider in chain.
- All providers exhausted → return cached-only result with a `stale=true` flag.

**Key rotation.** `ETHERSCAN_KEYS` is a comma-separated pool. Each key gets 5 req/sec. A pool of 5 = 25 req/sec free. Keys round-robin with per-key cooldown on 429.

**The Graph** handles all DeFi protocol data (Uniswap, Aave, Curve, bridges). Free, no rate limit, decentralized. Never use paid APIs for protocol-level data.

**Cache TTL strategy:**
- Txs older than 1000 blocks → cache permanently (blocks are immutable).
- Txs in last 1000 blocks → 5 min TTL.
- Wallet balance → 30 sec TTL.
- Labels → 1 hour TTL (to pick up community submissions).

---

## 9. Label Pipeline

Priority-ordered merge. First hit wins on conflict, but we return the full provenance chain.

1. **Hardcoded** (highest confidence): Tornado, Wormhole, Stargate, LayerZero endpoints, Uniswap routers, Binance/Coinbase/Kraken hot wallets, known exploit addresses.
2. **Community repos**: snapshot `brianleect/etherscan-labels` and `dawsbot/eth-labels` into Postgres on a weekly cron.
3. **Etherscan public tags**: scraped on-demand, cached 1h.
4. **Arkham free API**: on-demand, cached 1h.
5. **User submissions**: Postgres table `submitted_labels`, flagged for review above a confidence threshold.
6. **Heuristic**: e.g., "wallet sent to 50+ unique recipients, equal amounts → probable airdrop farmer" or "wallet received from Binance hot and then distributed → probable Binance user wallet".

---

## 10. AI Layer

**Role.** Format structured JSON output into readable prose. Nothing else.

**Provider abstraction.** `AIProvider` protocol with `generate(prompt, json_context) -> str`. Implementations: Groq (default), Ollama (offline), Claude, OpenAI.

**Prompt templates.**
- `trace_report` — given a trace tree, write an incident narrative.
- `profile_summary` — given risk + counterparties + behavior, write a 3-paragraph profile.
- `cluster_explanation` — given cluster + heuristic evidence, explain the link.

**Guardrails.**
- Prompts include "Do not speculate beyond provided JSON."
- Every number/address the LLM mentions must come from the JSON context (verified by regex post-check).
- If verification fails → regenerate once, then fall back to a templated report.

---

## 11. Chains Supported (Phase 1)

- **EVM (Covalent + chain explorer):** Ethereum, Polygon, Arbitrum, Base, BNB Chain.
- **Solana:** Alchemy.
- **Cross-chain:** known bridge contract registry for in/out matching (Stargate, Wormhole, LayerZero, Synapse, Across, Hop).

---

## 12. Real-Time Monitoring

- Alchemy Webhooks on wallet activity → FastAPI `/monitor/hook` → RQ job → WebSocket push to UI + Discord/Telegram notify.
- Moralis Streams as secondary provider.
- Alert rules: address-based, value-threshold, label-based ("alert when wallet X interacts with any mixer-labeled address").

---

## 13. Operational Concerns

**Deployment.** `docker-compose.yml` orchestrates Neo4j, Redis, Postgres, backend, frontend, Ollama, RQ worker. One-command self-host.

**Secrets.** All API keys in `.env`. No keys in git. Provide a `.env.example`.

**Rate-limit sanity.** Each provider module logs its own headroom. A `/health` endpoint exposes current key-pool state.

**Observability.** Structured JSON logs (request_id, route, chain, provider, cache_hit). Ship to any log aggregator via stdout.

**Testing.** Integration tests hit real testnet RPCs against fixed blocks — no mocks for provider behavior. Unit tests cover scoring, clustering, label-merge logic.

---

## 14. Security & Abuse

- No write-access to any chain — read-only forensics.
- Rate-limit investigation endpoints per-IP (Redis-backed).
- User-submitted labels gated behind review for public display; private labels per-user always allowed.
- Report-share links are unguessable (uuidv4) and optionally password-protected.
- Do not log full wallet contents in app logs (PII-ish in some jurisdictions).

---

## 15. Honest Limitations (surfaced in UI)

- **CEX deposits end the trail.** We report the deposit tx/block/timestamp for referral to law enforcement — we cannot see past KYC.
- **Mixer tracing is probabilistic only.** Every candidate is clearly flagged unconfirmed.
- **Label coverage grows over time.** Early investigations will see more `unlabeled` nodes; Neo4j persistence compounds coverage.
- **Privacy coins out of scope.** Monero/Zcash-shielded not supported.
- **No subpoena power.** Exchange KYC data requires law enforcement.

---

## 16. Milestones

| Phase | Scope | Exit criteria |
|---|---|---|
| **M0 — Skeleton** | repo, docker-compose, provider base, Neo4j upsert, one chain (ETH) | profile a hardcoded address end-to-end |
| **M1 — Hack Tracer** | traversal engine, terminal classifiers, bridge matching | trace Ronin/Harmony-style hack to terminals |
| **M2 — Wallet Profiler** | scoring, label pipeline (sources 1–3), counterparty map | risk-score 100 test wallets with ground-truth sanity |
| **M3 — AI reports** | Groq + Ollama adapters, prompt templates, guardrails | generate readable incident report for M1 trace |
| **M4 — Multi-chain** | Polygon, Arbitrum, Base, BNB, Solana | cross-chain trace across ≥2 chains via bridge |
| **M5 — Real-time** | Alchemy webhooks, alerts, WebSocket UI | live alert fires within 60s of wallet activity |
| **M6 — Clustering** | 4 heuristics, UI overlay | cluster detects known exchange-owned wallet group |
| **M7 — Polish** | report sharing, auth, rate-limit, docs | public alpha release |

---

## 17. Open Questions

1. **Auth model.** Public read-only demo vs. account-gated? Decision needed before M7.
2. **Incident registry.** Should we pre-seed Neo4j with `(:Incident)` nodes for famous hacks (Ronin, Harmony, Nomad, Wormhole) so traces auto-link? Strong yes-leaning, needs data source.
3. **Label submission trust.** Anonymous submissions with review queue, or require GitHub-OAuth to submit? Trust-vs-friction tradeoff.
4. **Bridge registry maintenance.** Manual curation vs. auto-discover from bridge contract event signatures? Start manual.
5. **Solana model.** Solana's account model doesn't map cleanly to the EVM wallet-tx graph. Need an adapter in `data/graph/` that normalizes Solana's (program, account, instruction) model into the same edge shape.

---

## 18. What this spec does NOT cover

- Frontend visual design language (Tailwind color tokens, typography) — separate design doc.
- Detailed prompt engineering for each report type — covered in `backend/ai/prompts/` when implemented.
- Exact Postgres schema DDL — covered in migrations when M0 starts.
- Deploy targets beyond docker-compose (k8s, Fly.io, Railway) — out of scope for v1.
