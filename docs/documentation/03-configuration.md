# Configuration

This document explains every environment variable ChainTrace reads, where to obtain the credentials, what free-tier limits apply, and what happens when a variable is missing. Copy `.env.example` to `.env` and fill in values before starting services.

---

## AI providers

ChainTrace uses AI only to format pre-analyzed JSON into prose. You need at least one AI provider configured. Groq is the recommended default — it is free and fast.

### `GROQ_API_KEY`

| | |
|---|---|
| **Purpose** | Primary AI provider — Llama 3.3 70B for report generation |
| **Where to get** | [console.groq.com](https://console.groq.com) — free account, no credit card |
| **Free tier** | 14,400 tokens/minute request limit on the free tier |
| **If missing** | AI report generation falls back to Ollama; if Ollama is also absent, `/report` returns HTTP 503 |

```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### `OLLAMA_BASE_URL`

| | |
|---|---|
| **Purpose** | Base URL for the local Ollama inference server |
| **Default** | `http://localhost:11434` |
| **Docker** | When running in Docker Compose, set to `http://ollama:11434` |
| **If missing** | Ollama provider is disabled; system uses Groq only |

```bash
OLLAMA_BASE_URL=http://localhost:11434
```

### `OLLAMA_MODEL`

| | |
|---|---|
| **Purpose** | Which model Ollama should use for generation |
| **Default** | `gemma3:4b` |
| **Options** | `gemma3:4b` (4GB), `phi4-mini:3.8b` (3.8GB), `qwen2.5:3b` (3GB) |
| **If missing** | Defaults to `gemma3:4b` |

```bash
OLLAMA_MODEL=gemma3:4b
```

To pre-pull the model before first use:

```bash
docker compose exec ollama ollama pull gemma3:4b
```

---

## Blockchain data APIs

ChainTrace uses a priority-ordered fallback chain: **Covalent → Alchemy → Etherscan family → Public RPC**. You need at least one of Covalent or Alchemy for meaningful functionality. Adding all three maximizes throughput on free tiers.

### `COVALENT_API_KEY`

| | |
|---|---|
| **Purpose** | Primary data provider — 100+ chains via unified GoldRush API |
| **Where to get** | [goldrush.dev](https://goldrush.dev) — free account |
| **Free tier** | 100 credits/month on free plan; each transaction history fetch = ~1 credit |
| **Chains** | Ethereum, Polygon, Arbitrum, Base, BNB Chain, and 95+ others |
| **If missing** | Covalent skipped; Alchemy becomes primary |

```bash
COVALENT_API_KEY=cqt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### `ALCHEMY_API_KEY`

| | |
|---|---|
| **Purpose** | Secondary data provider — ETH, Polygon, Arbitrum, Solana |
| **Where to get** | [alchemy.com](https://alchemy.com) — free account |
| **Free tier** | 300M compute units/month; typical trace = ~50k CUs |
| **Chains** | Ethereum, Polygon, Arbitrum, Optimism, Base, Solana |
| **If missing** | Alchemy skipped; Etherscan family becomes secondary |

```bash
ALCHEMY_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### `ETHERSCAN_KEYS`

| | |
|---|---|
| **Purpose** | Pool of Etherscan-family keys for per-chain explorers |
| **Where to get** | Register separate free accounts on each explorer |
| **Free tier** | 5 req/sec per key; 5 keys = 25 req/sec free |
| **Format** | Comma-separated list — no spaces |
| **If missing** | Etherscan family disabled; Public RPC becomes last resort |

**Register one key per explorer:**

| Explorer | URL | Chain |
|---|---|---|
| Etherscan | [etherscan.io/apis](https://etherscan.io/apis) | Ethereum |
| Polygonscan | [polygonscan.com/apis](https://polygonscan.com/apis) | Polygon |
| Arbiscan | [arbiscan.io/apis](https://arbiscan.io/apis) | Arbitrum |
| Basescan | [basescan.org/apis](https://basescan.org/apis) | Base |
| BscScan | [bscscan.com/apis](https://bscscan.com/apis) | BNB Chain |

```bash
ETHERSCAN_KEYS=AAAAAAAAAAAAAAAAAAAAAAAAAAA,BBBBBBBBBBBBBBBBBBBBBBBBBBB,CCCCCCCCCCCCCCCCCCCCCCCCCCC
```

Keys are round-robin rotated. On HTTP 429, the cooled key is skipped for 60 seconds.

### `ARKHAM_API_KEY`

| | |
|---|---|
| **Purpose** | Optional fourth label source — Arkham Intelligence address tags |
| **Where to get** | [intel.arkham.net](https://intel.arkham.net) — free account |
| **Free tier** | Limited query rate; labels are cached for 1 hour after first fetch |
| **If missing** | Arkham label source disabled; other four sources still operate |

```bash
ARKHAM_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Databases

### `NEO4J_URI`

| | |
|---|---|
| **Purpose** | Bolt connection string for Neo4j |
| **Default (local)** | `bolt://localhost:7687` |
| **Default (Docker)** | `bolt://neo4j:7687` (Docker Compose sets this automatically) |
| **If missing** | Backend crashes at startup — Neo4j is required |

```bash
NEO4J_URI=bolt://localhost:7687
```

### `NEO4J_PASSWORD`

| | |
|---|---|
| **Purpose** | Neo4j auth password (username is always `neo4j`) |
| **Default** | `forensic` (change for production) |
| **If missing** | Neo4j auth fails; backend crashes at startup |

```bash
NEO4J_PASSWORD=forensic
```

### `REDIS_URL`

| | |
|---|---|
| **Purpose** | Redis connection URL for cache, RQ job queue, and PubSub |
| **Default (local)** | `redis://localhost:6379` |
| **Default (Docker)** | `redis://redis:6379` (Docker Compose sets this automatically) |
| **If missing** | Backend crashes at startup — Redis is required |

```bash
REDIS_URL=redis://localhost:6379
```

### `POSTGRES_URL`

| | |
|---|---|
| **Purpose** | Async PostgreSQL DSN (asyncpg driver) |
| **Default (local)** | `postgresql+asyncpg://forensic:forensic@localhost:5432/forensic` |
| **Default (Docker)** | Set by Docker Compose using `POSTGRES_PASSWORD` |
| **If missing** | Label submissions and alert rule persistence fail; other functions continue |

```bash
POSTGRES_URL=postgresql+asyncpg://forensic:forensic@localhost:5432/forensic
```

### `POSTGRES_PASSWORD`

| | |
|---|---|
| **Purpose** | PostgreSQL password; used by Docker Compose to configure the container |
| **Default** | `forensic` (change for production) |

```bash
POSTGRES_PASSWORD=forensic
```

---

## Webhooks and monitoring

These are optional. Without them, real-time monitoring is disabled but all trace and profile functionality works normally.

### `DISCORD_WEBHOOK_URL`

| | |
|---|---|
| **Purpose** | Discord channel webhook for alert notifications |
| **Where to get** | Discord server settings → Integrations → Webhooks → New Webhook |
| **If missing** | Discord alerts disabled; Telegram still works if configured |

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/xxxxxxxxxxxx
```

### `TELEGRAM_BOT_TOKEN`

| | |
|---|---|
| **Purpose** | Telegram bot token for alert notifications |
| **Where to get** | [@BotFather](https://t.me/BotFather) on Telegram |
| **If missing** | Telegram alerts disabled |

```bash
TELEGRAM_BOT_TOKEN=1234567890:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### `TELEGRAM_CHAT_ID`

| | |
|---|---|
| **Purpose** | Chat ID where the bot should send alerts |
| **Where to get** | Send a message to your bot, then query `https://api.telegram.org/bot<token>/getUpdates` |
| **If missing** | Telegram alerts disabled even if `TELEGRAM_BOT_TOKEN` is set |

```bash
TELEGRAM_CHAT_ID=-100123456789
```

### `ALCHEMY_WEBHOOK_AUTH_TOKEN`

| | |
|---|---|
| **Purpose** | Verify inbound Alchemy webhook signatures to prevent spoofing |
| **Where to get** | Alchemy dashboard → Webhooks → your webhook → Auth token |
| **If missing** | Inbound webhook signature verification is skipped (accept all). **Set in production.** |

```bash
ALCHEMY_WEBHOOK_AUTH_TOKEN=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### `MORALIS_API_KEY`

| | |
|---|---|
| **Purpose** | Moralis Streams as a secondary real-time monitoring provider |
| **Where to get** | [moralis.io](https://moralis.io) — free account |
| **If missing** | Moralis Streams disabled; Alchemy webhooks still operate |

```bash
MORALIS_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Frontend

The frontend reads its own environment variables from `frontend/.env.local`. These are separate from the backend `.env` file.

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1
```

In production, replace `localhost:8000` with your backend's public URL.

---

## Production considerations

### Secrets management

Never commit `.env` to git. In production:

- **sops + age:** Encrypt `.env` with `sops --encrypt .env > .env.enc`, store the age private key in a secret manager.
- **direnv:** Use `.envrc` with `dotenv` for shell-level injection during development.
- **Docker secrets:** For Docker Swarm, mount secrets as files and read them in the application.

### Key rotation

Etherscan-family keys should be rotated every 6 months or whenever you suspect abuse. The `ETHERSCAN_KEYS` value is a comma-separated list — add new keys, remove old ones, restart the backend. No data migration needed.

### Rate-limit tuning

The `/health` endpoint reports current key pool size:

```bash
curl http://localhost:8000/health | jq .provider_pool
```

If `etherscan_keys` is below 3, you are at risk of provider exhaustion during heavy investigations. Add keys before running batch analysis.

### Neo4j memory

Default Neo4j Community heap is 512MB. For production workloads, set:

```yaml
# docker-compose.yml
neo4j:
  environment:
    NEO4J_server_memory_heap_initial__size: "1g"
    NEO4J_server_memory_heap_max__size: "4g"
    NEO4J_server_memory_pagecache_size: "2g"
```

---

## See also

- [02-getting-started.md](02-getting-started.md) — first-run walkthrough with minimum config
- [06-deployment.md](06-deployment.md) — production secrets injection and TLS
- [09-operations.md](09-operations.md) — what to do when providers are rate-limited
