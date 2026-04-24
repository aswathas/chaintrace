# Getting Started

This document walks you from a fresh clone to a working ChainTrace instance with all services running, verified, and ready to trace a real hack wallet. Expected time: 15–25 minutes depending on download speeds.

---

## Prerequisites

| Tool | Minimum version | Install |
|---|---|---|
| Docker | 24.x | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Docker Compose | v2 (plugin, not standalone) | bundled with Docker Desktop |
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) (needed only for local backend dev) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) (needed only for local frontend dev) |
| Git | any | system package manager |

If you only want to run ChainTrace (not develop it), you only need Docker and Docker Compose.

---

## Step 1: Clone the repository

```bash
git clone https://github.com/chaintrace/chaintrace.git
cd chaintrace
```

---

## Step 2: Configure environment variables

```bash
cp .env.example .env
```

Open `.env` in your editor. The minimum required variables to get a working instance:

```bash
# Minimum — AI (pick one)
GROQ_API_KEY=gsk_...           # Get free at console.groq.com

# Minimum — blockchain data (pick at least one)
COVALENT_API_KEY=...           # Get free at goldrush.dev
# OR
ALCHEMY_API_KEY=...            # Get free at alchemy.com

# Databases — leave as defaults for local dev
NEO4J_PASSWORD=forensic
POSTGRES_PASSWORD=forensic
```

See [03-configuration.md](03-configuration.md) for every variable, where to obtain keys, and what happens if a variable is missing.

---

## Step 3: Start all services

```bash
docker compose up
```

This starts Neo4j, Redis, PostgreSQL, the FastAPI backend, and the Next.js frontend. On first run, Docker will pull images and build the backend and frontend containers — this takes 3–5 minutes.

To also start Ollama (local AI, ~4GB model download):

```bash
docker compose --profile ollama up
```

Once running, you will see log lines from each service. Wait until you see:

```
backend_1  | INFO:     Application startup complete.
frontend_1 | ▲ Next.js ready on http://0.0.0.0:3000
```

---

## Step 4: Verify each service

### Neo4j

Open [http://localhost:7474](http://localhost:7474) in your browser. Log in with username `neo4j` and the password you set in `NEO4J_PASSWORD`. You should see the Neo4j Browser with an empty database.

### Redis

```bash
docker compose exec redis redis-cli ping
# Expected: PONG
```

### PostgreSQL

```bash
docker compose exec postgres psql -U forensic -d forensic -c '\dt'
# Expected: list of tables (may be empty on first run until migrations run)
```

### Backend health check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "redis": true,
  "neo4j": true,
  "provider_pool": {
    "etherscan_keys": 0,
    "covalent": true,
    "alchemy": false
  }
}
```

If `status` is `"degraded"`, check which service returned `false` and verify the corresponding container is healthy:

```bash
docker compose ps
```

### Frontend

Open [http://localhost:3000](http://localhost:3000). You should see the ChainTrace investigation UI.

---

## Step 5: Your first trace

We will trace the Ronin bridge hacker — one of the largest DeFi exploits in history. The attacker wallet on Ethereum is:

```
0x098B716B8Aaf21512996dC57EB0615e2383E2f96
```

### Option A: via curl

**Enqueue a profile job:**

```bash
curl -s -X POST http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -d '{"address": "0x098B716B8Aaf21512996dC57EB0615e2383E2f96", "chain": "eth"}' | jq .
```

Response:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

**Poll for the result** (replace with your `job_id`):

```bash
curl -s "http://localhost:8000/api/v1/profile/0x098B716B8Aaf21512996dC57EB0615e2383E2f96?chain=eth" | jq .
```

If the job is still running you will get `404`. Wait 10–30 seconds and retry.

**Enqueue a hack trace:**

```bash
curl -s -X POST http://localhost:8000/api/v1/trace \
  -H "Content-Type: application/json" \
  -d '{
    "seed": "0x098B716B8Aaf21512996dC57EB0615e2383E2f96",
    "chain": "eth",
    "max_hops": 5,
    "min_value_usd": 1000
  }' | jq .
```

**Poll for the trace result:**

```bash
JOB_ID="<your-job_id>"
curl -s "http://localhost:8000/api/v1/trace/${JOB_ID}" | jq .
```

**Generate an AI report** once the trace is complete:

```bash
curl -s -X POST "http://localhost:8000/api/v1/report/${JOB_ID}?kind=trace" | jq .report
```

### Option B: via the frontend UI

1. Navigate to [http://localhost:3000](http://localhost:3000)
2. Paste `0x098B716B8Aaf21512996dC57EB0615e2383E2f96` into the investigation input
3. Select chain `Ethereum`
4. Click **Trace** — the Cytoscape graph will populate hop-by-hop as the worker publishes updates

---

## Step 6: Local development (without Docker)

If you want to run the backend or frontend directly for faster iteration:

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend expects Neo4j, Redis, and Postgres to be reachable at the URLs in `.env`. You can still run those from Docker:

```bash
docker compose up neo4j redis postgres
```

### RQ Worker (required for async jobs)

In a second terminal:

```bash
cd backend
source .venv/bin/activate
rq worker --url redis://localhost:6379
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs at [http://localhost:3000](http://localhost:3000) with hot module reload.

---

## Common pitfalls

### "neo4j: false" in /health

Neo4j takes 20–30 seconds to initialize on first boot. The backend container has a `depends_on: condition: service_healthy` so it will not start until Neo4j passes its health check, but if you are running services manually, simply wait and retry.

### "No label found for address" on GET /labels

Labels are populated lazily — either from the hardcoded list (Tornado Cash, DEX routers, etc.) or after a profile job runs. If you have not yet profiled an address, there will be no label cached for it.

### 429 errors in backend logs immediately

Your provider key pool is exhausted. Add more keys to `ETHERSCAN_KEYS` or add a `COVALENT_API_KEY`. See [03-configuration.md](03-configuration.md) for free-tier limits per provider.

### Docker build fails on Apple Silicon (M1/M2)

Add `platform: linux/amd64` to the backend service in `docker-compose.yml` if you see architecture-related build errors. Neo4j 5 ships ARM images natively so that should not be an issue.

### "AI module not yet available" from /report

The `ai` module is not yet implemented (milestone M3). The endpoint returns HTTP 503 in this case. This is expected behavior during early development phases.

### RQ worker is not processing jobs

Ensure the worker is connected to the same Redis instance as the backend. If running locally (not Docker), run:

```bash
rq worker --url redis://localhost:6379
```

Check `docker compose logs backend` — you will see `rq_queue_ready` on startup if the queue initialized correctly.

---

## See also

- [03-configuration.md](03-configuration.md) — all environment variables with free-tier limits
- [04-api-reference.md](04-api-reference.md) — full endpoint documentation
- [09-operations.md](09-operations.md) — troubleshooting slow traces and provider issues
