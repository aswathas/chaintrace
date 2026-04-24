# Security

This document covers the ChainTrace security model: what threats we defend against, what controls are in place, what we explicitly do not protect, and how to report a vulnerability.

---

## Threat model

ChainTrace is a read-only forensics tool. It reads from public blockchains and public APIs, stores results locally, and serves them to users over HTTP. It does not control any funds, hold private keys, or have write access to any chain.

### Actors we defend against

| Actor | Threat | Control |
|---|---|---|
| External attacker | DoS via expensive trace jobs | Per-IP rate limiting (Redis-backed) on all investigation endpoints |
| External attacker | Probe internal services via the backend | Neo4j, Redis, Postgres not exposed externally; CORS restricted to frontend origin |
| External attacker | Forge inbound webhook events to trigger false alerts | HMAC-SHA256 signature verification on `/monitor/hook` |
| Malicious user | Label-submission abuse (flood or disinformation) | Submissions land in `pending` status; moderation queue before public display |
| Internal misconfiguration | API keys leaked via logs | PII/key scrubbing in structured log middleware; keys never logged |
| Operator | Accidental key commit | `.gitignore` includes `.env`; `.env.example` contains no real keys |

### What we explicitly do not defend against

- **Subpoena or legal compulsion.** If a government entity compels the operator to produce data, ChainTrace has no built-in resistance. The system is designed for legitimate security research — not for protecting criminal actors.
- **Nation-state-level traffic analysis.** ChainTrace makes API calls to Covalent, Alchemy, Etherscan, and Groq. An adversary monitoring those API providers could infer what addresses are being investigated.
- **Compromise of the host machine.** Once an attacker has host access, all API keys and database contents are accessible. This is a standard operational risk, not a ChainTrace-specific flaw.

---

## What we trust and what we don't

| Source | Trust level | Rationale |
|---|---|---|
| Public blockchain data (via providers) | High | Cryptographically verified; immutable |
| Covalent / Alchemy / Etherscan APIs | Medium | Trusted for data accuracy; rate limit and availability not guaranteed |
| Etherscan public address tags | Medium | Generally accurate; not cryptographically verified |
| Arkham Intelligence labels | Medium | Commercially curated; may lag behind recent events |
| Community GitHub label repos | Medium | Open-source; periodic snapshot; not real-time |
| User-submitted labels | Low | Anonymous; held in `pending` until reviewed |
| AI-generated report text | Low | Formatted from verified JSON; post-generation regex check enforces grounding |
| Inbound webhooks | Low until verified | HMAC signature check required before processing |

---

## Read-only chain access

ChainTrace never holds private keys. All blockchain interaction is read-only via public APIs and RPC endpoints. There is no functionality to sign transactions, submit transactions, or hold user funds.

This eliminates an entire class of attacks (private key theft, unauthorized fund movement) but does not eliminate data privacy concerns — see "What telemetry we emit" below.

---

## Secrets handling in code

**No secrets in source code.** All API keys and database credentials are loaded from environment variables via `pydantic-settings`. The `config.py` module uses `pydantic_settings.BaseSettings` which reads from the environment or `.env` file.

**No secrets in logs.** The `RequestLoggingMiddleware` sanitizes log output. The following are never logged:
- Full API keys (only whether they are set: `bool(key)`)
- Full wallet addresses in error messages where they could be PII
- Request/response bodies for label submission endpoints

**No secrets in Neo4j or Postgres.** API keys are not persisted to any database.

**`.env` in `.gitignore`.** The root `.gitignore` includes `.env`. Operators should verify this before initializing a public repository.

---

## What telemetry and logging we emit

ChainTrace emits structured JSON logs to stdout. Each log line contains:

- `request_id` — random UUID per request
- `method`, `path`, `status_code`, `duration_ms`
- `chain` — which blockchain was queried
- `provider` — which data provider was used
- `cache_hit` — whether Neo4j or Redis served the result

**What is NOT logged:**
- Full wallet addresses (only the chain, not the specific address investigated)
- Request bodies containing user-submitted labels
- API key values
- IP addresses beyond rate-limit tracking (not included in structured logs by default)

This logging posture is designed to be useful for operational debugging without creating an investigation diary that could itself be a liability.

---

## Label submission abuse

User-submitted labels via `POST /labels` present an abuse surface: a bad actor could submit false labels (e.g., label a clean exchange wallet as "darknet") to corrupt forensic conclusions.

**Controls:**

1. All submissions arrive with `status: "pending"` — they are never shown in the UI or returned from label lookups until approved by an operator.
2. Submissions are stored in `submitted_labels` with a timestamp and optional submitter ID.
3. The label source (`LabelSource.submission`) is always visible in the response — investigators can see that a label came from a community submission and weight it accordingly.
4. High-confidence sources (hardcoded, community repos, Etherscan) always take priority over submissions in the merge pipeline — a submission cannot override a hardcoded label.

---

## API rate limiting

All investigation endpoints (`/trace`, `/profile`, `/cluster`) are rate-limited per-IP using a Redis sliding window counter. The default is 60 requests per minute. This prevents:

- DoS via job queue flooding (each job consumes provider API quota)
- Enumeration attacks (bulk profiling of addresses)

The `/health`, `/labels/{address}` (GET), and `/monitor/alerts` (GET) endpoints are not rate-limited — they are cheap reads.

---

## Report share links

Report share links use UUIDv4 identifiers, which provide 122 bits of entropy. Brute-forcing a UUID space is computationally infeasible. Do not substitute sequential integers.

Optional password protection for report links is planned for M7. Until then, treat report URLs as unguessable but not secret — anyone with the link can read the report.

---

## Known security caveats

1. **No authentication in v1.** ChainTrace ships without a user authentication system. If you expose your instance to the internet, use HTTP Basic Auth at the reverse proxy layer or restrict access by IP. Full auth is planned for M7.

2. **Neo4j browser is exposed at port 7474 by default.** In the Docker Compose development configuration, the Neo4j Browser is accessible at `http://localhost:7474`. Do not expose port 7474 publicly on production deployments.

3. **AI guardrails are best-effort.** The post-generation regex check that verifies AI report grounding catches most hallucinations but is not a formal proof. Do not treat AI-generated report text as authoritative — it is a prose rendering of the structured data, which is the authoritative source.

4. **Webhook endpoint is unauthenticated if `ALCHEMY_WEBHOOK_AUTH_TOKEN` is not set.** The `/monitor/hook` endpoint accepts any JSON payload. Set the auth token in production.

5. **Label data accuracy is not guaranteed.** Community labels, Etherscan tags, and Arkham labels may be incorrect, outdated, or incomplete. Always verify critical attribution against primary on-chain evidence.

---

## Vulnerability disclosure

If you discover a security vulnerability in ChainTrace, please report it responsibly:

1. **Email:** aswathas20@gmail.com with subject line `[SECURITY] ChainTrace vulnerability`
2. **Include:** Description of the vulnerability, steps to reproduce, potential impact, and any suggested mitigations
3. **Do not:** Open a public GitHub issue for security vulnerabilities — use email until a patch is available
4. **Response time:** Acknowledgment within 48 hours; fix timeline communicated within 7 days

There is no bug bounty program at this time (open-source project). Credit will be given in release notes unless you prefer anonymity.

---

## See also

- [06-deployment.md](06-deployment.md) — hardening checklist for production deployments
- [03-configuration.md](03-configuration.md) — `ALCHEMY_WEBHOOK_AUTH_TOKEN` and secrets configuration
- [10-limitations.md](10-limitations.md) — limitations relevant to forensic conclusions
