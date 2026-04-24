# Operations Runbook

This document is a practical runbook for ChainTrace operators. Each section addresses a specific symptom, explains the likely cause, and provides commands to diagnose and resolve it.

---

## Quick reference — service ports

| Service | Port | Interface |
|---|---|---|
| Backend | 8000 | `curl http://localhost:8000/health` |
| Frontend | 3000 | Browser `http://localhost:3000` |
| Neo4j Browser | 7474 | Browser (dev only — do not expose publicly) |
| Neo4j Bolt | 7687 | Used by backend internally |
| Redis | 6379 | `redis-cli` |
| PostgreSQL | 5432 | `psql` |
| Ollama | 11434 | `curl http://localhost:11434/api/tags` |

---

## "My trace is slow"

**Symptom:** A `POST /trace` job takes more than 60 seconds or does not complete within 10 minutes.

**Diagnosis:**

```bash
# Check current RQ job status
docker compose exec redis redis-cli llen rq:queue:default
# High number (>10) = queue backlog — need more workers

# Check which provider is being used
docker compose logs backend --tail 100 | grep '"provider"'
# If you see "public_rpc" repeatedly — all premium providers are down or rate-limited

# Check provider pool headroom
curl http://localhost:8000/health | python3 -m json.tool
```

**Resolution:**

If queue is backed up — add more RQ workers:

```bash
# In a new terminal or background process
docker compose exec backend rq worker --url redis://redis:6379 &
docker compose exec backend rq worker --url redis://redis:6379 &
```

If provider is falling back to public RPC — check API key exhaustion:

```bash
docker compose logs backend --tail 200 | grep '"429"'
# Count 429s per provider to identify which pool is exhausted
```

Add more Etherscan keys to `ETHERSCAN_KEYS` in `.env`, then restart:

```bash
docker compose restart backend
```

If the trace itself is traversing too many wallets — reduce `max_hops` or increase `min_value_usd` in the trace request to filter small transactions.

---

## "All providers returning 429"

**Symptom:** Every provider API call returns 429. Backend falls back to public RPC for everything. Traces are slow or incomplete.

**Diagnosis:**

```bash
docker compose logs backend | grep "429" | tail -50
# Identify which provider and keys are cooling

# Check how many Etherscan keys are configured
curl http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['provider_pool']['etherscan_keys'])"
```

**Resolution:**

Etherscan key pool exhausted — register more free keys:

```bash
# Add to .env:
ETHERSCAN_KEYS=key1,key2,key3,key4,key5,key6,key7,key8,key9,key10
# Restart backend to reload the pool
docker compose restart backend
```

Covalent quota exhausted (100 credits/month on free tier):

```bash
# Register a second Covalent account and add the key
# Covalent key rotation is a planned feature; currently only one key is supported
# Workaround: remove Covalent until next month, rely on Alchemy + Etherscan
```

Alchemy CU exhausted — check Alchemy dashboard at [dashboard.alchemy.com](https://dashboard.alchemy.com):

```bash
# Create a second Alchemy app and swap the key
ALCHEMY_API_KEY=new-key-here
docker compose restart backend
```

Temporary cooldown — keys cool for 60 seconds per 429. If you are running a heavy batch investigation, wait 60 seconds and retry:

```bash
sleep 60 && curl -X POST http://localhost:8000/api/v1/trace ...
```

---

## "AI report is gibberish or empty"

**Symptom:** `POST /report/{job_id}` returns incoherent text, the AI makes up addresses not in the trace, or the endpoint returns HTTP 503.

**Diagnosis:**

```bash
# Check if AI module is available
curl http://localhost:8000/api/v1/report/some-job-id -X POST 2>&1
# 503 = AI module not implemented yet (milestone M3)
# 200 with bad text = provider issue or guardrail failure

# Check Groq API connectivity
curl -s -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer ${GROQ_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "ping"}]}' \
  | python3 -m json.tool
```

**Resolution:**

If Groq is down or rate-limited — switch to Ollama:

```bash
# Start Ollama if not running
docker compose --profile ollama up -d ollama

# Pull the model
docker compose exec ollama ollama pull gemma3:4b

# Set Ollama as the fallback
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=gemma3:4b
docker compose restart backend
```

If the guardrail check is failing (AI inventing data not in context) — the report generation falls back to a templated format automatically after two failed attempts. If the templated fallback is also missing, the AI module is not yet implemented (expected in milestone M3).

If Groq free-tier rate limit is hit (14,400 tokens/minute):

```bash
# Wait 60 seconds and retry
# Or register a second Groq account for a separate key
```

---

## "Neo4j is running out of disk space"

**Symptom:** Neo4j logs show disk warnings, or Docker volume is near capacity.

**Diagnosis:**

```bash
# Check volume size
docker system df -v | grep neo4j_data

# Check Neo4j database size from inside the container
docker compose exec neo4j du -sh /data/databases/

# Count nodes and relationships
docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD}" \
  "MATCH (n) RETURN count(n) AS nodes"
docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD}" \
  "MATCH ()-[r]->() RETURN count(r) AS relationships"
```

**Resolution:**

Delete transaction edges older than a retention threshold (keep wallet nodes, remove old SENT edges to free space):

```cypher
// Delete SENT edges older than 365 days
MATCH ()-[s:SENT]->()
WHERE s.timestamp < datetime() - duration('P365D')
DELETE s
```

```bash
docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD}" \
  "MATCH ()-[s:SENT]->() WHERE s.timestamp < datetime() - duration('P365D') DELETE s"
```

Delete unlabeled wallet nodes that have no remaining edges:

```bash
docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD}" \
  "MATCH (w:Wallet) WHERE NOT (w)-[]-() AND w.labels = [] DELETE w"
```

If disk is critically full — stop Neo4j, resize the Docker volume or attach additional storage, restart:

```bash
docker compose stop neo4j
# resize volume or mount additional disk
docker compose start neo4j
```

---

## "Redis OOM (out of memory)"

**Symptom:** Redis logs `OOM command not allowed when used memory > 'maxmemory'`. Cache writes fail. RQ jobs may stall.

**Diagnosis:**

```bash
docker compose exec redis redis-cli info memory | grep used_memory_human
docker compose exec redis redis-cli info memory | grep maxmemory
```

**Resolution:**

Set `maxmemory` and eviction policy so Redis self-manages:

```bash
docker compose exec redis redis-cli config set maxmemory 2gb
docker compose exec redis redis-cli config set maxmemory-policy allkeys-lru
```

This evicts the least-recently-used cache keys when memory is full. RQ job data is stored separately and is not subject to LRU eviction (RQ keys have no TTL by default).

Make this permanent in `docker-compose.yml`:

```yaml
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

If Redis is being used to store large trace results that should be in Neo4j — ensure `data/graph/upsert.py` is persisting results correctly and that trace results in Redis have appropriate TTLs (24h, not permanent).

---

## "Worker queue is backed up"

**Symptom:** Jobs stay in `queued` status for minutes. `rq:queue:default` has a high length.

**Diagnosis:**

```bash
docker compose exec redis redis-cli llen rq:queue:default
# Number of pending jobs

docker compose exec redis redis-cli smembers rq:workers
# Set of active worker IDs — empty if no workers running
```

**Resolution:**

Start additional workers:

```bash
# Scale workers in Docker Compose (add a worker service)
docker compose exec backend sh -c "rq worker --url redis://redis:6379 &"

# Or scale via Docker Compose service (if a worker service is defined)
docker compose up --scale worker=4 -d
```

Kill stuck or failed jobs:

```bash
# View failed jobs
docker compose exec redis redis-cli lrange rq:queue:failed 0 -1

# Requeue all failed jobs
docker compose exec backend rq requeue --all --queue default
```

Check for jobs hitting the timeout (600s for trace, 300s for profile/cluster):

```bash
docker compose logs backend | grep "job_timeout"
# If trace jobs are timing out, reduce max_hops or add more workers
```

---

## "Profile returns 404 for an address I've investigated before"

**Symptom:** `GET /profile/{address}` returns 404 after a previous successful profile.

**Cause:** Profile results are stored in Redis with a 5-minute TTL. After expiry, the profile must be re-run via `POST /profile`.

**Resolution:**

Re-submit the profile job:

```bash
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -d '{"address": "0x...", "chain": "eth"}'
```

Note: The re-run will be much faster than the first time because the wallet's transaction history is already in Neo4j — no provider API calls needed.

If you want profiles to persist longer, increase the TTL in `data/cache/redis_cache.py`:

```python
# Change profile TTL from 300 to 3600 (1 hour)
TTL_PROFILE = 3600
```

---

## "Docker Compose services keep restarting"

**Diagnosis:**

```bash
docker compose ps
docker compose logs <service-name> --tail 50
```

**Common causes:**

- **Backend**: Missing required env var (e.g., `NEO4J_PASSWORD` not set). Check `config.py` validation errors in logs.
- **Neo4j**: Insufficient memory. Reduce heap settings or increase VPS RAM.
- **Postgres**: Data directory permissions issue. Check `docker compose logs postgres`.

---

## "Alchemy webhooks are not triggering alerts"

**Diagnosis:**

```bash
# Verify webhook endpoint is reachable from the internet
curl -X POST https://chaintrace.yourdomain.com/api/v1/monitor/hook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Check if webhook auth token is causing rejection
docker compose logs backend | grep "webhook"
```

**Resolution:**

If the endpoint is not reachable — ensure your reverse proxy is routing `/api/v1/monitor/hook` to the backend and that port 443 is open.

If HMAC verification is failing — verify `ALCHEMY_WEBHOOK_AUTH_TOKEN` matches the token in your Alchemy dashboard.

If the webhook is received but no alert fires — check that a matching rule exists:

```bash
curl http://localhost:8000/api/v1/monitor/alerts
```

---

## See also

- [03-configuration.md](03-configuration.md) — API key setup and rate limit information
- [06-deployment.md](06-deployment.md) — backup and TLS setup
- [07-security.md](07-security.md) — webhook signature verification
