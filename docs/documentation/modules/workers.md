# Workers Module

**Location:** `backend/workers/`

## Purpose

RQ (Redis Queue) job runners for long-running investigations. Bridge synchronous RQ task queue to async core engines (tracer, profiler, clusterer). Return results to Redis for HTTP polling and WebSocket streaming.

## Public API

### `trace_job.py`

**`run_trace(job_id: str, seed: str, chain: str, opts: dict) -> dict`**
RQ synchronous job. Executes async hack tracer via `asyncio.run()`. Upserts results to Neo4j. Stores in Redis with 1-hour expiry. Publishes completion to Redis pub/sub.

**Signature:**
```python
def run_trace(job_id: str, seed: str, chain: str, opts: dict) -> dict
```

**Inputs:**
- `job_id` — unique job identifier (uuidv4)
- `seed` — wallet address or tx hash to start trace
- `chain` — blockchain (ethereum, polygon, arbitrum, etc.)
- `opts` — dict with optional keys: max_hops, min_value_usd, fanout

**Outputs:** TraceResult dict (compatible with backend.models.trace).

**Side effects:**
- Calls `asyncio.run(trace(...))` — core tracer engine
- Calls `asyncio.run(upsert_trace(...))` — upserts nodes/edges to Neo4j
- Stores result in Redis: `trace:{job_id}` with 3600s expiry
- Publishes to Redis pubsub: `trace:{job_id}:stream` → `{"status": "complete", "hops": N}`

**Error handling:** Exceptions caught and logged; job marked failed in RQ.

### `profile_job.py`

**`run_profile(job_id: str, address: str, chain: str, opts: dict) -> dict`**
RQ synchronous job. Profiles wallet (risk score, behavior, counterparties). Similar pattern to trace_job.

**Inputs:**
- `job_id`, `address`, `chain`, `opts` (limit, include_history)

**Outputs:** ProfileResult dict.

**Side effects:**
- Fetches wallet txs from graph/providers
- Computes risk score, behavior tags, counterparties
- Stores in Redis: `profile:{job_id}`
- Publishes to pubsub: `profile:{job_id}:stream`

### `cluster_job.py`

**`run_cluster(job_id: str, addresses: list[str], chain: str, opts: dict) -> dict`**
RQ synchronous job. Run clustering heuristics around wallet set.

**Inputs:**
- `job_id`, `addresses` (wallet addresses to cluster), `chain`, `opts`

**Outputs:** ClusterResult dict.

## Algorithm & Data Flow

```
HTTP Request Flow:

POST /trace → FastAPI handler
├─ validate request (seed, chain)
├─ job_id = uuid4()
├─ enqueue: q.enqueue(run_trace, job_id, seed, chain, opts)
└─ return {"job_id": job_id, "status": "queued"}

RQ Worker processes run_trace:
├─ asyncio.run(trace(seed, chain, **opts))
├─ result = TraceResult object
├─ asyncio.run(upsert_trace(result, chain))
├─ redis.set(f"trace:{job_id}", json.dumps(result), ex=3600)
├─ redis.publish(f"trace:{job_id}:stream", json.dumps({"status": "complete", ...}))
└─ return result

HTTP Polling:

GET /trace/{job_id} → FastAPI handler
├─ redis.get(f"trace:{job_id}")
├─ if found: return cached TraceResult
├─ else: return {"status": "pending"} or {"status": "error"}

WebSocket Streaming:

GET /trace/{job_id}/stream [WS] → FastAPI handler
├─ subscribe to Redis pubsub: f"trace:{job_id}:stream"
├─ push updates to client as they arrive
├─ on completion: send final result + close connection
```

## Dependencies

**Imports:**
- `redis.Redis` — queue management + result storage
- `asyncio` — bridge to async core engines
- `json` — serialization
- `backend.core.tracer.engine` — `trace()` function
- `backend.core.profiler.summary` — `summarize()` function (for profiler job)
- `backend.core.clustering.merger` — `cluster_wallets()` function (for cluster job)
- `backend.data.graph.upsert` — `upsert_trace()` etc.

**Imported by:**
- `backend.main` — RQ worker registration
- `backend.api.routes.*` — job enqueue calls

## Extension Points

1. **Add new job type:** Create `{task}_job.py` with synchronous `run_{task}()` function. Register in RQ worker.
2. **Streaming updates:** Call `redis.publish(f"{task_id}:stream", update_json)` mid-execution for progress reporting.
3. **Result TTL:** Adjust `ex=3600` in `redis.set()` for longer/shorter result retention.
4. **Retry logic:** Wrap job in try/except with retry counter; re-enqueue on failure.

## Testing Guidance

**Unit tests:**
- Mock `asyncio.run()` to return fixed trace/profile results
- Mock Redis to verify `set()` and `publish()` calls
- Verify job enqueue returns job_id
- Test error case (exception in core engine)

**Integration:**
- Run RQ worker: `rq worker default`
- Enqueue via HTTP: POST /trace
- Poll: GET /trace/{job_id}
- Verify result in Redis after completion
- Verify Neo4j upsert (MATCH (w:Wallet) COUNT(*))
- Test WebSocket stream subscription during job execution

## Known Gaps & TODOs

- `trace_job.py:5` — `trace()` and `upsert_trace()` imports assumed to exist; wire to actual backend modules
- `profile_job.py`, `cluster_job.py` — likely stubs; implementation incomplete
- No explicit retry logic (job fails permanently on exception)
- No progress callback (can't update frontend mid-execution)
- No job timeout enforcement (long-running job may hang RQ worker)
- No priority queue (all jobs enqueued to default queue)
- No job dependency tracking (can't run job B only after job A completes)

## See Also

- `tracer.md` — core engine called by trace_job
- `profiler.md` — core engine called by profile_job
- `clustering.md` — core engine called by cluster_job
- `data-graph.md` — upsert functions persist job results
