# Graph Report - /mnt/c/Users/aswat/OneDrive/Desktop/Projects/Forensic_Tool_versio  (2026-04-24)

## Corpus Check
- 152 files · ~51,836 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 935 nodes · 1586 edges · 31 communities detected
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 567 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_AI Providers & Models|AI Providers & Models]]
- [[_COMMUNITY_Data Provider Adapters|Data Provider Adapters]]
- [[_COMMUNITY_AI Layer Architecture|AI Layer Architecture]]
- [[_COMMUNITY_Clustering & Heuristics|Clustering & Heuristics]]
- [[_COMMUNITY_API Routes & Middleware|API Routes & Middleware]]
- [[_COMMUNITY_Tracer Engine|Tracer Engine]]
- [[_COMMUNITY_Clustering Algorithms|Clustering Algorithms]]
- [[_COMMUNITY_AI Provider Code|AI Provider Code]]
- [[_COMMUNITY_Arkham Label Source|Arkham Label Source]]
- [[_COMMUNITY_Alchemy Webhook Monitor|Alchemy Webhook Monitor]]
- [[_COMMUNITY_AI Prompt Templates|AI Prompt Templates]]
- [[_COMMUNITY_Graph DB Layer|Graph DB Layer]]
- [[_COMMUNITY_Deployment & Secrets|Deployment & Secrets]]
- [[_COMMUNITY_Trace Request Flow|Trace Request Flow]]
- [[_COMMUNITY_ABI Decoder|ABI Decoder]]
- [[_COMMUNITY_Frontend API Client|Frontend API Client]]
- [[_COMMUNITY_Test Fixtures|Test Fixtures]]
- [[_COMMUNITY_Hardcoded Label Tests|Hardcoded Label Tests]]
- [[_COMMUNITY_Risk Scorer Tests|Risk Scorer Tests]]
- [[_COMMUNITY_Settings  Config|Settings / Config]]
- [[_COMMUNITY_Alerts API|Alerts API]]
- [[_COMMUNITY_Incident Data Model|Incident Data Model]]
- [[_COMMUNITY_Contributor Workflow|Contributor Workflow]]
- [[_COMMUNITY_httpx dependency|httpx dependency]]
- [[_COMMUNITY_tenacity dependency|tenacity dependency]]
- [[_COMMUNITY_python-dotenv dependency|python-dotenv dependency]]
- [[_COMMUNITY_Frontend API URL|Frontend API URL]]
- [[_COMMUNITY_Labels Endpoint|Labels Endpoint]]
- [[_COMMUNITY_K8s Deployment|K8s Deployment]]
- [[_COMMUNITY_Prometheus Metrics|Prometheus Metrics]]
- [[_COMMUNITY_Code of Conduct|Code of Conduct]]

## God Nodes (most connected - your core abstractions)
1. `Chain` - 56 edges
2. `RQ worker jobs for long-running investigations.` - 51 edges
3. `RedisCache` - 35 edges
4. `TokenTransfer` - 35 edges
5. `Transaction` - 35 edges
6. `ProviderError` - 34 edges
7. `RateLimitError` - 31 edges
8. `AlertEvent` - 22 edges
9. `Label` - 18 edges
10. `EtherscanProvider` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Hack Tracer (README description)` --semantically_similar_to--> `Hack Tracer Module`  [INFERRED] [semantically similar]
  README.md → CLAUDE.md
- `Wallet Profiler (README description)` --semantically_similar_to--> `Wallet Profiler Module`  [INFERRED] [semantically similar]
  README.md → CLAUDE.md
- `Design Principles (README)` --semantically_similar_to--> `Rationale: AI is a formatter, not an analyst`  [INFERRED] [semantically similar]
  README.md → CLAUDE.md
- `Rationale: Why AI is a formatter not an analyst` --semantically_similar_to--> `Rationale: AI is a formatter, not an analyst`  [INFERRED] [semantically similar]
  docs/documentation/01-architecture.md → CLAUDE.md
- `Rationale: Why Neo4j as both database and cache` --semantically_similar_to--> `Rationale: Neo4j as both database and cache`  [INFERRED] [semantically similar]
  docs/documentation/01-architecture.md → CLAUDE.md

## Hyperedges (group relationships)
- **Provider Fallback Chain (Covalent -> Alchemy -> Etherscan -> RPC)** — 01_architecture_covalent, 01_architecture_alchemy, 01_architecture_etherscan_family, 01_architecture_thegraph, 01_architecture_public_rpc, 01_architecture_fallback_chain_rationale [EXTRACTED 1.00]
- **Async Trace Pipeline: Route -> RQ -> Provider -> Neo4j -> Redis -> WS** — 04_api_reference_post_trace, 04_api_reference_trace_job_worker, 01_architecture_data_ingestion_layer, 01_architecture_neo4j, 01_architecture_redis, 04_api_reference_ws_trace_stream [EXTRACTED 1.00]
- **Three Persistence Layers (Neo4j + Postgres + Redis)** — 01_architecture_neo4j, 01_architecture_postgres, 01_architecture_redis, 05_data_model_wallet_node, 05_data_model_alert_rules_table, 05_data_model_redis_cache_keys [EXTRACTED 1.00]
- **Provider fallback chain (Covalent -> Alchemy -> Etherscan -> RPC)** —  [EXTRACTED 1.00]
- **Four clustering heuristics merged via union-find** —  [EXTRACTED 1.00]
- **6-source priority-ordered label pipeline** —  [EXTRACTED 1.00]

## Communities

### Community 0 - "AI Providers & Models"
Cohesion: 0.02
Nodes (116): Claude Provider (stub), GroqProvider, llama-3.3-70b-versatile, AI Layer Module, Ollama local models (gemma3:4b, phi4-mini:3.8b, qwen2.5:3b), OllamaProvider, OpenAI Provider (stub), cluster_explanation prompt template (+108 more)

### Community 1 - "Data Provider Adapters"
Cohesion: 0.06
Nodes (62): AlchemyProvider, Alchemy API provider — ETH, Polygon, Arbitrum, Base, Solana., Implements Provider using the Alchemy v2/v3 API., Alert rule and event models., Provider, ProviderError, ProviderExhausted, RateLimitError (+54 more)

### Community 2 - "AI Layer Architecture"
Cohesion: 0.03
Nodes (95): Rationale: Why AI is a formatter not an analyst, AI Layer (Groq/Ollama), Alchemy Provider, Async Trace/Profile Data Flow, Component Diagram, Covalent Provider, Data Ingestion Layer, Etherscan Family Provider Pool (+87 more)

### Community 3 - "Clustering & Heuristics"
Cohesion: 0.04
Nodes (59): gas_price_fingerprint(), has_round_amounts(), is_high_velocity(), Stateless behavioral helper functions for the profiler., True if avg inter-tx gap < 10 minutes and tx count > 20 in any 24h window., True if >= threshold fraction of txs have a round USD value (multiple of 10)., Days since wallet first appeared on-chain., Histogram of gas prices normalised to [0, 1] — used for fingerprint clustering. (+51 more)

### Community 4 - "API Routes & Middleware"
Cohesion: 0.05
Nodes (48): BaseHTTPMiddleware, Enum, label_key(), profile_key(), Cache key builders for consistent Redis key naming., trace_key(), LabelSource, Label and label-source models. (+40 more)

### Community 5 - "Tracer Engine"
Cohesion: 0.1
Nodes (44): BridgeEdge, _chains_to_search(), match_bridge_out(), Cross-chain bridge deposit → withdrawal matching., Minimal representation of a bridge deposit edge — provided by the tracer engine., Return candidate destination chains given the deposit's bridge label., Given a bridge deposit edge, find the recipient address on the destination chain, # TODO: wire to backend.data.providers.fallback.FallbackChain when available (+36 more)

### Community 6 - "Clustering Algorithms"
Cohesion: 0.08
Nodes (27): RQ job: run entity clustering around a seed address., Synchronous RQ job to cluster wallets around a seed., run_cluster(), ClusterEdge, find_co_spend_clusters(), Co-spend clustering — wallets appearing together as inputs/outputs in ≥3 txs., Find address pairs that co-appear in ≥3 transactions.      multi_party_txs: list, ClusterEdge (+19 more)

### Community 7 - "AI Provider Code"
Cohesion: 0.09
Nodes (23): ClaudeProvider, Anthropic Claude provider (optional)., Call Claude and return prose., Claude API via Anthropic SDK., Exception, GroqProvider, Groq API provider (Llama 3.3 70B). Primary AI backend., Call Groq API and return prose. (+15 more)

### Community 8 - "Arkham Label Source"
Cohesion: 0.1
Nodes (28): fetch_arkham_label(), Arkham Intelligence free API label fetcher — source 4 of the label pipeline., Call Arkham free API for entity label; cache result 1 hour., # TODO: wire to backend.data.cache.redis_cache when available, # TODO: wire to httpx when available, # TODO: cache null, # TODO: cache: await redis_cache.set(cache_key, label.__dict__, ttl=3600), Label (+20 more)

### Community 9 - "Alchemy Webhook Monitor"
Cohesion: 0.1
Nodes (24): _chain_from_network(), parse_alchemy_webhook(), Map Alchemy network string to chain name., Parse Alchemy wallet activity webhook. Returns AlertEvent., AlertEvent, AlertRule, notify(), _publish_pubsub() (+16 more)

### Community 10 - "AI Prompt Templates"
Cohesion: 0.08
Nodes (23): Cluster explanation prompt template., Render a cluster explanation prompt pair., render_cluster_explanation(), generate_report(), get_prompt_template(), _post_check_passes(), Verify every 0x-address and dollar value in prose appears in JSON context., Return a minimal templated report when LLM fails. (+15 more)

### Community 11 - "Graph DB Layer"
Cohesion: 0.08
Nodes (23): close_driver(), get_driver(), Neo4j async driver singleton., Return the singleton async Neo4j driver, creating it if needed., Close the driver on shutdown., get_neo4j(), get_pg(), get_redis() (+15 more)

### Community 12 - "Deployment & Secrets"
Cohesion: 0.08
Nodes (27): Caddy/Traefik Reverse Proxy, Single-node Deployment Topology, ALCHEMY_WEBHOOK_AUTH_TOKEN env var, Secrets Management (sops, age, direnv), Label pydantic schema, LabelSource enum, workers.monitor_job.process_webhook, POST /labels submission endpoint (+19 more)

### Community 13 - "Trace Request Flow"
Cohesion: 0.09
Nodes (24): First Trace (Ronin bridge hacker example), Address pydantic schema, workers.cluster_job.run_cluster, GET /profile/{address} endpoint, GET /trace/{job_id} endpoint, POST /cluster endpoint, POST /profile endpoint, POST /report/{job_id} endpoint (+16 more)

### Community 14 - "ABI Decoder"
Cohesion: 0.12
Nodes (20): _abi_selector(), decode_call(), DecodedCall, _minimal_decode(), ABI decoding — selector matching for top ERC20/ERC721 + common router methods., Decode fixed-size 32-byte ABI words for named params., Compute the 4-byte selector hex string for a function ABI entry., # TODO: replace with eth_hash.auto.keccak(sig.encode()).hex()[:8] when available (+12 more)

### Community 15 - "Frontend API Client"
Cohesion: 0.16
Nodes (6): ApiClient, fetchData(), fetchProfile(), handleCreateRule(), handleDeleteRule(), handleToggleRule()

### Community 17 - "Test Fixtures"
Cohesion: 0.25
Nodes (7): client(), neo4j_driver(), Pytest fixtures for backend tests., Provide a Neo4j driver. Skip if unavailable., Provide FastAPI TestClient for integration tests., Provide a fake Redis client (fakeredis)., redis_client()

### Community 18 - "Hardcoded Label Tests"
Cohesion: 0.25
Nodes (7): Unit tests for hardcoded label resolution., Verify Uniswap v2 router label resolution., Verify known CEX hot wallet labels resolve., Verify Tornado Cash pool addresses resolve correctly., test_hardcoded_cex_hot_wallets(), test_hardcoded_tornado_cash(), test_hardcoded_uniswap_v2_router()

### Community 19 - "Risk Scorer Tests"
Cohesion: 0.25
Nodes (7): Unit tests for wallet risk scorer., Verify weight arithmetic and clamping to [0, 100]., Verify risk level thresholds: 0-24 low, 25-49 medium, 50-74 high, 75+ critical., Verify scorer module imports without error., test_scorer_import(), test_scorer_thresholds(), test_scorer_weights()

### Community 20 - "Settings / Config"
Cohesion: 0.4
Nodes (4): BaseSettings, get_settings(), Settings loader — single source of truth for all env vars., Settings

### Community 21 - "Alerts API"
Cohesion: 0.5
Nodes (5): AlertRule pydantic schema, GET /monitor/alerts endpoint, POST /monitor endpoint, alert_events table, alert_rules table

### Community 22 - "Incident Data Model"
Cohesion: 0.5
Nodes (4): Neo4j :Incident Node, incidents table, Neo4j :PART_OF Relationship, Neo4j :Transaction Node

### Community 45 - "Contributor Workflow"
Cohesion: 1.0
Nodes (2): Dev Workflow (branches, commits, PRs), Running Tests (unit + integration)

### Community 57 - "httpx dependency"
Cohesion: 1.0
Nodes (1): httpx>=0.27

### Community 58 - "tenacity dependency"
Cohesion: 1.0
Nodes (1): tenacity>=8.3 retry

### Community 59 - "python-dotenv dependency"
Cohesion: 1.0
Nodes (1): python-dotenv>=1.0

### Community 60 - "Frontend API URL"
Cohesion: 1.0
Nodes (1): Frontend NEXT_PUBLIC_API_URL env

### Community 61 - "Labels Endpoint"
Cohesion: 1.0
Nodes (1): GET /labels/{address} endpoint

### Community 62 - "K8s Deployment"
Cohesion: 1.0
Nodes (1): Kubernetes Deployment Sketch

### Community 63 - "Prometheus Metrics"
Cohesion: 1.0
Nodes (1): Prometheus /metrics (planned M7)

### Community 64 - "Code of Conduct"
Cohesion: 1.0
Nodes (1): Code of Conduct

## Knowledge Gaps
- **266 isolated node(s):** `Settings loader — single source of truth for all env vars.`, `Verify every 0x-address and dollar value in prose appears in JSON context.`, `Return a minimal templated report when LLM fails.`, `Cluster explanation prompt template.`, `Render a cluster explanation prompt pair.` (+261 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Contributor Workflow`** (2 nodes): `Dev Workflow (branches, commits, PRs)`, `Running Tests (unit + integration)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `httpx dependency`** (1 nodes): `httpx>=0.27`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `tenacity dependency`** (1 nodes): `tenacity>=8.3 retry`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `python-dotenv dependency`** (1 nodes): `python-dotenv>=1.0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Frontend API URL`** (1 nodes): `Frontend NEXT_PUBLIC_API_URL env`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Labels Endpoint`** (1 nodes): `GET /labels/{address} endpoint`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `K8s Deployment`** (1 nodes): `Kubernetes Deployment Sketch`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Prometheus Metrics`** (1 nodes): `Prometheus /metrics (planned M7)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Code of Conduct`** (1 nodes): `Code of Conduct`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RQ worker jobs for long-running investigations.` connect `Data Provider Adapters` to `Clustering & Heuristics`, `API Routes & Middleware`, `AI Provider Code`, `Arkham Label Source`, `Alchemy Webhook Monitor`, `AI Prompt Templates`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `RedisCache` connect `API Routes & Middleware` to `Graph DB Layer`, `Clustering Algorithms`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `KeyPool` connect `Clustering & Heuristics` to `Data Provider Adapters`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `Chain` (e.g. with `AlchemyProvider` and `Alchemy API provider — ETH, Polygon, Arbitrum, Base, Solana.`) actually correct?**
  _`Chain` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `RQ worker jobs for long-running investigations.` (e.g. with `GroqProvider` and `OllamaProvider`) actually correct?**
  _`RQ worker jobs for long-running investigations.` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `RedisCache` (e.g. with `FastAPI application entrypoint.` and `Start and tear down Neo4j + Redis connections.`) actually correct?**
  _`RedisCache` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `TokenTransfer` (e.g. with `AlchemyProvider` and `Alchemy API provider — ETH, Polygon, Arbitrum, Base, Solana.`) actually correct?**
  _`TokenTransfer` has 33 INFERRED edges - model-reasoned connections that need verification._