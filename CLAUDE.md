# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ChainTrace** — an open-source, self-hostable multi-chain blockchain forensics tool. Positioned as a free alternative to Chainalysis for security researchers, small teams, and internship/academic use. Two core modules: **Hack Tracer** (trace stolen funds hop-by-hop across chains) and **Wallet Profiler** (risk score any address with labels, counterparty analysis, behavior patterns).

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Next.js Frontend                    │
│         Cytoscape.js (graph viz) + Tailwind          │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────┐
│               FastAPI Backend (Python)               │
│  /trace  /profile  /cluster  /monitor  /report      │
└──┬──────────┬──────────┬───────────┬────────────────┘
   │          │          │           │
   ▼          ▼          ▼           ▼
Neo4j      Redis      PostgreSQL   AI Layer
(graph)   (cache)     (labels,    (Groq API /
                      metadata)    Ollama local)
   │
   ▼
Data Ingestion Layer
   ├── Covalent API       (100+ chains, unified)
   ├── Alchemy API        (ETH, Polygon, Arbitrum, Solana)
   ├── Etherscan family   (per-chain, key rotation)
   ├── The Graph          (DeFi protocol data, free)
   └── Public RPCs        (chainlist.org, fallback)
```

## Tech Stack

- **Backend:** Python 3.11+ with FastAPI (async)
- **Graph DB:** Neo4j Community (wallet → transaction → wallet relationships)
- **Cache:** Redis (aggressive TTL caching — old txs cached forever, recent txs 5min TTL)
- **Relational DB:** PostgreSQL (wallet labels, risk scores, cluster groups, alert configs)
- **Frontend:** Next.js 14 + TypeScript + Cytoscape.js + Tailwind CSS
- **AI Layer:** Groq API (primary, free — Llama 3.3 70B) / Ollama (local fallback — gemma3:4b, phi4-mini:3.8b, qwen2.5:3b)
- **Queue:** Redis Queue (RQ) for async investigation jobs
- **Monitoring:** Alchemy Webhooks + Moralis Streams for real-time alerts

## Key Design Decisions

**AI is a formatter, not an analyst.** All intelligence (graph traversal, risk scoring, label matching, cluster detection) lives in Python code. The LLM receives pre-analyzed structured JSON and writes readable prose. This works with small models like gemma3:4b.

**Neo4j is both database and cache.** Once a wallet is investigated and stored in Neo4j, repeat investigations require zero API calls. The graph grows smarter over time.

**Multi-API fallback chain:** Covalent → Alchemy → Etherscan family → Public RPC. On rate limit (429), automatically rotate to next key in pool, then next provider.

**API key rotation for free limits:** Register 5+ free keys per provider (Etherscan, Polygonscan, Arbiscan, Basescan, BscScan — one key per chain explorer). Each key = 5 req/sec. Pool of 5 = 25 req/sec free.

**The Graph Protocol for DeFi data:** All Uniswap/Aave/Curve/bridge interaction data comes from The Graph subgraphs (free, no rate limits, decentralized). Never use paid APIs for protocol-level data.

## Module Structure (Planned)

```
backend/
  api/
    routes/          # FastAPI route handlers
  core/
    tracer/          # Hack Tracer — hop-by-hop fund flow traversal
    profiler/        # Wallet Profiler — risk scoring, label lookup
    clustering/      # Entity clustering heuristics
    labeler/         # 5-source label pipeline
    parser/          # Smart contract ABI decoding + attack pattern matching
    monitor/         # Real-time wallet monitoring via webhooks
  data/
    providers/       # Covalent, Alchemy, Etherscan, TheGraph adapters
    cache/           # Redis cache layer with TTL strategy
    graph/           # Neo4j client + query helpers
  ai/
    providers/       # Groq, Ollama, Claude, OpenAI adapters
    prompts/         # Structured prompt templates for report generation
  models/            # Pydantic schemas

frontend/
  app/               # Next.js app router
  components/
    graph/           # Cytoscape.js transaction graph
    profiler/        # Wallet profile cards
    tracer/          # Hack investigation UI
    alerts/          # Real-time monitoring UI
```

## Label Sources (Priority Order)

1. Hardcoded known contracts (Tornado Cash, major bridges, DEX routers, CEX hot wallets)
2. Community GitHub repos (`brianleect/etherscan-labels`, `dawsbot/eth-labels`)
3. Etherscan public address tags
4. Arkham Intelligence free API
5. Community-contributed labels (user submissions stored in PostgreSQL)
6. Heuristic auto-labeling (behavior patterns → inferred labels)

## Supported Chains (Phase 1)

EVM chains via Covalent + chain-specific explorers: Ethereum, Polygon, Arbitrum, Base, BNB Chain. Solana via Alchemy. Cross-chain bridge detection via known bridge contract addresses.

## Risk Scoring Logic

Rule-based scoring (0–100) using weighted signals:
- Mixer interaction (Tornado Cash etc.) → +40 points
- Darknet-labeled counterparty → +35 points
- Known exploit wallet interaction → +30 points
- High-velocity small transactions → +15 points
- Round-amount transfers → +10 points
- Recently created wallet → +5 points
- Verified protocol interaction → -10 points
- CEX-labeled counterparty → -5 points

## Mixer Tracing Strategy

Tornado Cash uses fixed denominations (0.1, 1, 10, 100 ETH). On deposit detection, scan withdrawal events for same denomination within 72-hour window. Surface probabilistic exit candidates in UI — clearly labeled as unconfirmed.

## Entity Clustering Heuristics

1. Common funder: wallets funded from same source → cluster
2. Behavioral fingerprint: same gas price + timing patterns → cluster
3. Nonce-linked: contract deployer + funder → cluster
4. Co-spend: wallets that always transact together → cluster

## Development Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Neo4j (Docker)
docker run -p 7474:7474 -p 7687:7687 neo4j:community

# Redis (Docker)
docker run -p 6379:6379 redis:alpine

# PostgreSQL (Docker)
docker run -p 5432:5432 -e POSTGRES_PASSWORD=forensic neo4j postgres:16

# Ollama (local AI)
ollama pull gemma3:4b
ollama serve

# Run all services
docker-compose up
```

## Environment Variables

```
# AI (configure one or more)
GROQ_API_KEY=           # Free at console.groq.com — primary AI provider
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b

# Blockchain Data APIs (all free tier)
COVALENT_API_KEY=       # goldrush.dev
ALCHEMY_API_KEY=        # alchemy.com
ETHERSCAN_KEYS=key1,key2,key3,key4,key5   # comma-separated pool

# Databases
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://localhost:5432/forensic

# Alerts
DISCORD_WEBHOOK_URL=    # optional
TELEGRAM_BOT_TOKEN=     # optional
```

## Honest Limitations

- **CEX deposits end the trail.** Flag with block/timestamp for law enforcement use.
- **Mixer tracing is probabilistic only.** Always labeled as unconfirmed in UI.
- **Label coverage starts thin.** Grows with every investigation via Neo4j persistence.
- **No subpoena power.** Exchange KYC data requires law enforcement action.
- **Privacy coins (Monero) are untraceable.** Do not claim otherwise.
