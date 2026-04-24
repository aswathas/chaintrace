# Contributing

This document covers how to contribute to ChainTrace: repository layout, development workflow, testing, coding style, and how to extend the system with new chains, label sources, and risk-score signals.

---

## Repo layout

```
/
├── backend/
│   ├── api/
│   │   ├── routes/          # FastAPI route handlers (trace, profile, cluster, monitor, report, labels)
│   │   ├── deps.py          # Shared FastAPI dependencies (get_redis, get_rq_queue, get_neo4j)
│   │   └── middleware.py    # RequestLoggingMiddleware, rate limiting
│   ├── core/
│   │   ├── tracer/          # Hop-by-hop traversal engine
│   │   ├── profiler/        # Risk scoring, counterparty analysis
│   │   ├── clustering/      # Entity clustering heuristics
│   │   ├── labeler/         # 6-source label pipeline
│   │   ├── parser/          # ABI decoding, exploit pattern matching
│   │   └── monitor/         # Webhook dispatch, alert evaluation
│   ├── data/
│   │   ├── providers/       # Covalent, Alchemy, Etherscan, TheGraph, RPC adapters + rotator
│   │   ├── cache/           # Redis cache layer with TTL strategy
│   │   └── graph/           # Neo4j driver, queries, idempotent upsert
│   ├── ai/
│   │   ├── providers/       # Groq, Ollama, Claude, OpenAI adapters
│   │   └── prompts/         # Report prompt templates
│   ├── models/              # Pydantic schemas
│   ├── workers/             # RQ job entrypoints
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # pydantic-settings config
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js 14 app router
│   ├── components/          # Cytoscape wrapper, profile cards, alert UI
│   └── lib/                 # API client, WebSocket client
├── docs/
│   ├── documentation/       # This directory
│   └── superpowers/specs/   # Design specification
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Dev workflow

### Branch naming

```
feat/<short-description>     # new feature
fix/<short-description>      # bug fix
chore/<short-description>    # tooling, deps, config
docs/<short-description>     # documentation only
```

Examples:
- `feat/add-polygon-provider`
- `fix/etherscan-key-rotation-cooldown`
- `docs/api-reference-update`

### Commits

Use imperative mood, present tense. One-line summary ≤ 72 characters. Optional body for context:

```
Add Polygon provider with key rotation

Implements the PolygonScanProvider subclass of EtherscanBase.
Key pool reads from ETHERSCAN_KEYS with chain_id filtering.
```

### PR process

1. Fork the repo and create your branch from `main`
2. Write tests before implementing (for core logic — not for route handlers)
3. Run the test suite: `pytest backend/tests -v`
4. Ensure `tsc --noEmit` passes in `frontend/`
5. Open a PR against `main` with a description covering: what changes, why, and how to test it
6. A maintainer will review within 3 business days

---

## Running tests

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

Test categories:
- `tests/unit/` — pure Python, no external dependencies. Covers: `scorer.py`, `labeler/merge.py`, `data/providers/rotator.py`, all clustering heuristics.
- `tests/integration/` — hits real testnet RPCs against fixed block numbers. Requires `ALCHEMY_API_KEY` or `COVALENT_API_KEY` in environment. Covers: provider fetching, Neo4j upsert/query, end-to-end trace on known testnet transactions.

**Do not mock provider behavior in integration tests.** The value of integration tests is verifying that the provider adapters actually work against live endpoints.

```bash
# Unit tests only (no API keys needed)
pytest tests/unit -v

# Integration tests (needs at least one data API key)
ALCHEMY_API_KEY=xxx pytest tests/integration -v
```

### Frontend

```bash
cd frontend
npm install
npx tsc --noEmit          # type check
npm run build             # full Next.js build (catches runtime errors)
```

---

## Coding style

**Python:**
- Type hints on all function signatures. Return types required.
- `async def` for all I/O-bound functions (provider calls, Neo4j queries, Redis operations).
- One-line docstrings only. Describe the contract, not the implementation.
- No premature abstractions. Build the specific thing before extracting a general pattern.
- `structlog` for all logging — no `print()`, no `logging.getLogger()`.
- Pydantic v2 models for all request/response types and data contracts between modules.

```python
async def fetch_txs(self, address: str, chain: str) -> list[Transaction]:
    """Return all outbound transactions for address on chain."""
    ...
```

**TypeScript:**
- Strict mode enabled in `tsconfig.json`.
- No `any`. Use `unknown` and narrow.
- Server components for data-fetching pages; client components only when interactivity requires it.

---

## How to add a new chain

Adding chain support touches four areas:

### 1. Add the chain to the `ChainEnum`

```python
# models/wallet.py
class ChainEnum(str, Enum):
    eth      = "eth"
    polygon  = "polygon"
    arbitrum = "arbitrum"
    base     = "base"
    bnb      = "bnb"
    solana   = "solana"
    optimism = "optimism"   # ← new
```

### 2. Add a provider subclass

```python
# data/providers/etherscan.py
class OptimisticEtherscanProvider(EtherscanBase):
    BASE_URL = "https://api-optimistic.etherscan.io/api"
    CHAIN_ID = 10
```

Register it in `data/providers/fallback.py`:

```python
CHAIN_PROVIDERS = {
    ...
    "optimism": [CovalentProvider, AlchemyProvider, OptimisticEtherscanProvider, PublicRPCProvider],
}
```

### 3. Add a Cytoscape color for the chain

```typescript
// frontend/components/graph/legend.ts
export const CHAIN_COLORS: Record<string, string> = {
  eth:       "#627eea",
  polygon:   "#8247e5",
  arbitrum:  "#28a0f0",
  base:      "#0052ff",
  bnb:       "#f0b90b",
  solana:    "#9945ff",
  optimism:  "#ff0420",  // ← new
};
```

### 4. Add integration test

```python
# tests/integration/test_optimism_provider.py
async def test_fetch_txs_optimism():
    provider = OptimisticEtherscanProvider(api_key="...")
    txs = await provider.fetch_txs("0x...", "optimism")
    assert len(txs) > 0
```

---

## How to add a new label source

Label sources live in `backend/core/labeler/`. Each source implements the `LabelSource` protocol:

```python
# core/labeler/base.py
class LabelSourceProtocol(Protocol):
    async def resolve(self, address: str, chain: str) -> Optional[Label]:
        """Return a label for address, or None if unknown."""
        ...
```

Steps:

1. Create `backend/core/labeler/my_source.py` implementing the protocol.
2. Add the source to `labeler/merge.py` in the priority-ordered list.
3. Add a `LabelSource` enum value in `models/label.py`.
4. Write a unit test in `tests/unit/test_labeler_my_source.py`.

The merge function uses first-hit semantics — place your new source at the appropriate priority level (after hardcoded, before heuristic, at the priority that matches its confidence level).

---

## How to add a new risk-score signal

Risk score signals are defined in `backend/core/profiler/scorer.py` as a list of `(signal_fn, weight)` tuples:

```python
SIGNALS = [
    (has_mixer_interaction,        +40),
    (has_darknet_counterparty,     +35),
    (has_exploit_wallet_link,      +30),
    (is_high_velocity_small_tx,    +15),
    (has_round_amount_transfers,   +10),
    (is_recently_created,          +5),
    (has_verified_protocol,        -10),
    (has_cex_counterparty,         -5),
]
```

To add a signal:

1. Write a function `my_signal(wallet_data: WalletData) -> bool` in `scorer.py`.
2. Add it to `SIGNALS` with a weight. The total is clamped to `[0, 100]`.
3. Add the signal to the `scoring_breakdown` dict in the profile response model.
4. Write a unit test with a wallet fixture that triggers the signal.

Keep weights proportional to existing ones. A new signal should not dominate the score unless it is truly exceptional evidence.

---

## Code of conduct

ChainTrace is a research and security tool. We expect contributors to:

- Engage respectfully and in good faith
- Not use ChainTrace or its development to facilitate harm
- Report security issues privately before public disclosure

We follow the [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). Violations should be reported to aswathas20@gmail.com.

---

## See also

- [01-architecture.md](01-architecture.md) — invariants you must not break
- [05-data-model.md](05-data-model.md) — Neo4j schema if you touch graph queries
- [Design specification](../superpowers/specs/chaintrace-design.md) — authoritative source for module structure
