# ChainTrace

**Free, self-hostable multi-chain blockchain forensics tool for security researchers and incident response teams.**

ChainTrace is a self-hosted alternative to Chainalysis, designed for researchers, small teams, and academic use. It traces stolen funds hop-by-hop across blockchains and profiles wallets for risk and behavior patterns—all without closed APIs or expensive subscriptions.

---

## What It Does

**Hack Tracer** — Given a known exploit or theft wallet, ChainTrace recursively traces fund flows across chains. It follows the largest outflows, detects terminal destinations (CEX deposits, mixers, bridges, cold storage), and maps probabilistic mixer exits.

**Wallet Profiler** — Analyze any address with a risk score (0–100), behavioral labels, counterparty links, and transaction patterns. Understand whether a wallet is a user account, bot, exchange, or exploit artifact.

**Real-Time Monitor** — Set alert rules on wallet activity via Alchemy webhooks or Moralis streams. Get Discord/Telegram notifications when monitored wallets move funds.

---

## Architecture

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
┌──────────────────────────────────────────────┐
│           Data Ingestion Layer                │
│  Covalent → Alchemy → Etherscan fam → RPC    │
│  + The Graph (DeFi protocol data)            │
└──────────────────────────────────────────────┘
```

**Tech Stack:**
- Backend: Python 3.11+ / FastAPI (async)
- Graph DB: Neo4j Community
- Cache + Queue: Redis + RQ
- Relational: PostgreSQL
- Frontend: Next.js 14 + TypeScript + Cytoscape.js
- AI: Groq API (Llama 3.3 70B) or Ollama (local)

---

## Quickstart

### 1. Start Services

```bash
docker-compose up
```

Starts Neo4j, Redis, PostgreSQL, backend FastAPI, frontend Next.js, and Ollama.

### 2. Verify Backend

```bash
curl http://localhost:8000/health
```

### 3. Investigate a Wallet

```bash
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -d '{"address": "0x...", "chain": "ethereum"}'
```

### 4. Trace Stolen Funds

```bash
curl -X POST http://localhost:8000/trace \
  -H "Content-Type: application/json" \
  -d '{"seed": "0x...", "chain": "ethereum", "max_hops": 10}'
```

---

## Environment Variables

```bash
# AI (choose at least one)
GROQ_API_KEY=                      # Free tier at console.groq.com
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b

# Blockchain Data APIs (free tier)
COVALENT_API_KEY=                  # goldrush.dev
ALCHEMY_API_KEY=                   # alchemy.com
ETHERSCAN_KEYS=key1,key2,key3      # Comma-separated pool (free rate limit)

# Databases
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://localhost:5432/forensic

# Alerts (optional)
DISCORD_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

## Design Principles

**AI is a formatter, not an analyst.** All traversal, scoring, labeling, and clustering are deterministic Python code. The LLM only formats pre-analyzed JSON into prose. This enables offline operation and reproducibility.

**Neo4j as both cache and database.** Once a wallet is investigated, its neighborhood is persisted. Repeat investigations = zero external API calls. The graph grows smarter over time.

**Multi-provider fallback.** On HTTP 429 (rate limit), automatically rotate API keys, then escalate to the next provider. Chain: Covalent → Alchemy → Etherscan family → public RPC.

**Free at scale.** Register 5+ free API keys per provider (Etherscan, Polygonscan, Arbiscan). Each = 5 req/sec free. A pool of 5 keys = 25 req/sec free.

---

## Supported Chains (Phase 1)

**EVM:** Ethereum, Polygon, Arbitrum, Base, BNB Chain (via Covalent + chain explorers)

**Solana:** Via Alchemy

**Cross-chain:** Detected bridges — Stargate, Wormhole, LayerZero, Synapse, Across, Hop

---

## Honest Limitations

- **CEX deposits end the trail.** We report the deposit tx/block/timestamp for law enforcement referral — we cannot see past KYC walls.
- **Mixer tracing is probabilistic.** All candidates are flagged "unconfirmed mixer exit."
- **Label coverage grows over time.** Early investigations see more unlabeled nodes; Neo4j persistence compounds coverage.
- **Privacy coins out of scope.** Monero and Zcash shielded transactions are not supported.
- **No subpoena power.** Exchange KYC data requires law enforcement action.

---

## Testing

```bash
pytest backend/tests -v
```

All tests include type hints. Unit tests cover scoring, labeling, and key rotation. Integration tests hit real testnet RPCs.

---

## Contributing

Contributions welcome. See the spec at `/docs/superpowers/specs/chaintrace-design.md`.

- Fork the repo
- Create a feature branch
- Open a PR with tests

---

## License

MIT. Use freely for research, incident response, and academic purposes.

---

**Questions?** Open an issue or contact aswathas20@gmail.com.
