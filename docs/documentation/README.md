# ChainTrace Documentation

ChainTrace is a free, self-hostable multi-chain blockchain forensics tool. It gives security researchers, incident-response teams, and students a capable alternative to Chainalysis without closed APIs or subscription fees. Two core modules — **Hack Tracer** and **Wallet Profiler** — run on your own infrastructure against public blockchain data.

---

## What this covers

This directory is the canonical documentation hub for ChainTrace. Every significant decision, interface, and operational concern is covered here. The source of truth for architecture decisions is always the design spec at [`/docs/superpowers/specs/chaintrace-design.md`](../superpowers/specs/chaintrace-design.md).

---

## Table of contents

| File | What it covers |
|---|---|
| [01-architecture.md](01-architecture.md) | Component diagram, data flow, design rationale, deployment topology |
| [02-getting-started.md](02-getting-started.md) | Dev setup, first `docker compose up`, first real trace |
| [03-configuration.md](03-configuration.md) | Every environment variable explained with links to API consoles |
| [04-api-reference.md](04-api-reference.md) | All endpoints with request/response JSON examples and WebSocket frames |
| [05-data-model.md](05-data-model.md) | Neo4j schema, Postgres tables, Redis key catalog, TTL policy |
| [06-deployment.md](06-deployment.md) | VPS production setup, TLS, backups, secrets, observability hardening |
| [07-security.md](07-security.md) | Threat model, abuse controls, secrets handling, vulnerability disclosure |
| [08-contributing.md](08-contributing.md) | Dev workflow, testing, how to add a chain / label source / risk signal |
| [09-operations.md](09-operations.md) | Operator runbook — slow trace, 429 storms, OOM, queue backlog |
| [10-limitations.md](10-limitations.md) | Honest capability boundaries surfaced in the UI |

### Module deep-dives (`modules/`)

_These are populated as each module reaches M1+ maturity._

| File | Module |
|---|---|
| `modules/hack-tracer.md` | Hop-by-hop traversal engine, terminal detection, bridge matching |
| `modules/wallet-profiler.md` | Risk scoring signals, label pipeline, counterparty map |
| `modules/entity-clustering.md` | Four heuristics, union-find merge, confidence thresholds |
| `modules/ai-layer.md` | Provider abstraction, prompt templates, guardrail verification |
| `modules/real-time-monitor.md` | Alchemy webhooks, Moralis Streams, alert dispatch |

---

## Choose your own adventure

### I am an operator setting up ChainTrace on a VPS

Start with [02-getting-started.md](02-getting-started.md) to get services running locally, then jump to [06-deployment.md](06-deployment.md) for production hardening. Read [03-configuration.md](03-configuration.md) to understand every key you need to obtain.

### I am a contributor adding a feature or fixing a bug

Read [01-architecture.md](01-architecture.md) first — it explains the invariants you must not break. Then read [08-contributing.md](08-contributing.md) for workflow, testing, and coding style. The specific module deep-dives in `modules/` are relevant if you are touching a particular subsystem.

### I am a security researcher using ChainTrace for an investigation

Start at [04-api-reference.md](04-api-reference.md) to understand the API surface. Read [10-limitations.md](10-limitations.md) before drawing any conclusions — the CEX terminal wall, probabilistic mixer tracing, and label coverage gaps all directly affect what you can and cannot conclude.

### I am evaluating ChainTrace for my team or project

The project pitch: ChainTrace is the open-source answer to the $50k/year forensics SaaS problem. It runs on a $20/month VPS, uses only free-tier blockchain APIs, and grows smarter with every investigation because every result is persisted in Neo4j. It will not replace a court-backed investigation, but it will let you trace a hack to its terminal destinations and generate a readable incident report without any vendor lock-in.

---

## See also

- [Design specification](../superpowers/specs/chaintrace-design.md) — the authoritative source for architecture decisions
- [Root README](../../README.md) — project pitch and quickstart
- [CLAUDE.md](../../CLAUDE.md) — guidance for AI-assisted development in this repo
