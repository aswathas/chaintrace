# Deployment

This document covers running ChainTrace in production: VPS setup, TLS termination, secret injection, backups, observability, and a hardening checklist. Development setup is covered in [02-getting-started.md](02-getting-started.md).

---

## VPS setup (recommended path)

A $20/month VPS (4 vCPU, 8GB RAM, 80GB SSD) is sufficient for single-investigator workloads. Tested on Ubuntu 22.04 LTS. Neo4j requires at least 4GB of heap — scale the machine if you plan to store more than ~500k wallet nodes.

### 1. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Clone the repository

```bash
git clone https://github.com/chaintrace/chaintrace.git /opt/chaintrace
cd /opt/chaintrace
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — fill in API keys, set strong passwords
nano .env
```

Minimum production changes from the example:

```bash
NEO4J_PASSWORD=<strong-random-password>
POSTGRES_PASSWORD=<strong-random-password>
GROQ_API_KEY=<your-key>
COVALENT_API_KEY=<your-key>
ALCHEMY_WEBHOOK_AUTH_TOKEN=<your-token>
```

### 4. Set Neo4j memory limits

Edit `docker-compose.yml` to add memory configuration for Neo4j:

```yaml
neo4j:
  environment:
    NEO4J_AUTH: "neo4j/${NEO4J_PASSWORD}"
    NEO4J_PLUGINS: '["apoc"]'
    NEO4J_server_memory_heap_initial__size: "1g"
    NEO4J_server_memory_heap_max__size: "4g"
    NEO4J_server_memory_pagecache_size: "2g"
```

### 5. Start services

```bash
docker compose up -d
docker compose ps        # verify all services are healthy
curl http://localhost:8000/health
```

### 6. Set up TLS with Caddy

Caddy handles HTTPS automatically via Let's Encrypt. Install and configure it on the host:

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
apt install caddy
```

`/etc/caddy/Caddyfile`:

```
chaintrace.yourdomain.com {
    reverse_proxy /api/* localhost:8000
    reverse_proxy /* localhost:3000

    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }
}
```

```bash
systemctl enable caddy
systemctl start caddy
```

### Alternative: Traefik

If you prefer Traefik as part of Docker Compose (useful for multi-service VPS setups):

```yaml
# Add to docker-compose.yml
traefik:
  image: traefik:v3
  command:
    - "--providers.docker=true"
    - "--entrypoints.web.address=:80"
    - "--entrypoints.websecure.address=:443"
    - "--certificatesresolvers.le.acme.email=aswathas20@gmail.com"
    - "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json"
    - "--certificatesresolvers.le.acme.tlschallenge=true"
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - traefik_letsencrypt:/letsencrypt

backend:
  labels:
    - "traefik.http.routers.backend.rule=Host(`chaintrace.yourdomain.com`) && PathPrefix(`/api`)"
    - "traefik.http.routers.backend.tls.certresolver=le"
    - "traefik.http.services.backend.loadbalancer.server.port=8000"

frontend:
  labels:
    - "traefik.http.routers.frontend.rule=Host(`chaintrace.yourdomain.com`)"
    - "traefik.http.routers.frontend.tls.certresolver=le"
    - "traefik.http.services.frontend.loadbalancer.server.port=3000"
```

---

## Kubernetes sketch

Kubernetes is not the primary deployment target for ChainTrace v1. The following is a community-contributed starting point, not a production-vetted configuration.

The recommended K8s approach is:

- **Neo4j:** Use the official [Neo4j Helm chart](https://neo4j.com/docs/operations-manual/current/kubernetes/) with persistent volume claims.
- **Redis:** Use [Bitnami Redis chart](https://github.com/bitnami/charts/tree/main/bitnami/redis) in standalone mode (cluster mode is unnecessary at this scale).
- **PostgreSQL:** Use [Bitnami PostgreSQL chart](https://github.com/bitnami/charts/tree/main/bitnami/postgresql) with a persistent volume.
- **Backend/Frontend:** Standard Deployment + Service + Ingress.
- **RQ Worker:** Separate Deployment with the same backend image, override `command` to `rq worker --url redis://redis:6379`.

Secrets should be injected via Kubernetes Secrets or an external secrets operator (External Secrets Operator + AWS Secrets Manager / HashiCorp Vault).

---

## Secret injection

### sops + age (recommended for VPS)

```bash
# Install sops
curl -LO https://github.com/getsops/sops/releases/latest/download/sops-v3.x.x.linux.amd64
chmod +x sops-v3.x.x.linux.amd64 && mv sops-v3.x.x.linux.amd64 /usr/local/bin/sops

# Generate age key
age-keygen -o ~/.age/key.txt

# Encrypt .env
sops --encrypt --age $(cat ~/.age/key.txt | grep public | awk '{print $4}') .env > .env.enc

# Decrypt at deploy time
sops --decrypt .env.enc > .env
```

Store `.env.enc` in git. Keep the age private key out of git — store it in a password manager or CI secrets.

### direnv (development)

```bash
# .envrc
dotenv .env
```

```bash
direnv allow .
```

---

## Backup strategy

### Neo4j

Neo4j Community does not include online backup. Use volume-level backups:

```bash
# Stop neo4j container before backup to ensure consistency
docker compose stop neo4j

# Create timestamped backup archive
tar -czf /backups/neo4j-$(date +%Y%m%d-%H%M%S).tar.gz \
  $(docker volume inspect chaintrace_neo4j_data -f '{{.Mountpoint}}')

# Restart
docker compose start neo4j
```

Schedule via cron (daily at 02:00):

```cron
0 2 * * * /opt/chaintrace/scripts/backup-neo4j.sh
```

For production workloads, Neo4j Enterprise supports online backups. As an alternative, consider exporting the graph periodically to Cypher dump format:

```bash
docker compose exec neo4j neo4j-admin database dump neo4j --to-path=/backups/
```

### PostgreSQL

```bash
docker compose exec postgres pg_dump -U forensic forensic \
  | gzip > /backups/postgres-$(date +%Y%m%d-%H%M%S).sql.gz
```

### Redis

Redis data is ephemeral cache by design. The only durable Redis content is `monitor:rules`. If you need persistence, enable AOF in Redis:

```yaml
# docker-compose.yml
redis:
  command: redis-server --appendonly yes
```

Or export rules to Postgres (planned feature): alert rules are already stored in the `alert_rules` Postgres table, so Redis is reconstructible from Postgres on restart.

---

## Observability

### Structured logging

The backend emits structured JSON logs via `structlog`. Each log line includes:

```json
{
  "event": "request_complete",
  "request_id": "8f3a2b...",
  "method": "POST",
  "path": "/api/v1/trace",
  "status_code": 202,
  "duration_ms": 14,
  "chain": "eth",
  "provider": "covalent",
  "cache_hit": false
}
```

Collect from stdout to any log aggregator:

```bash
# Ship to Loki (Grafana stack)
docker compose logs -f backend | promtail --stdin

# Ship to Papertrail
docker compose logs -f | logger -n logs.papertrail.com -P 12345 -t chaintrace

# Local file rotation
docker compose logs -f backend >> /var/log/chaintrace/backend.log
```

### Prometheus metrics

The `/metrics` endpoint (if exposed — planned for M7) will expose:

- `chaintrace_trace_jobs_total` — counter by status (queued/complete/failed)
- `chaintrace_provider_requests_total` — counter by provider and chain
- `chaintrace_provider_429_total` — rate-limit hits per provider
- `chaintrace_neo4j_cache_hits_total` — Neo4j-first cache hit rate
- `chaintrace_rq_queue_length` — current RQ backlog depth

Until `/metrics` is available, scrape RQ metrics via `rq info --url redis://localhost:6379`.

---

## Hardening checklist

### Network

- [ ] Neo4j ports (7474, 7687) are NOT exposed to the public internet — bind to `127.0.0.1` or use Docker internal networking only
- [ ] Redis port (6379) is NOT exposed to the public internet
- [ ] PostgreSQL port (5432) is NOT exposed to the public internet
- [ ] Only ports 80 and 443 are open externally (via Caddy/Traefik)
- [ ] Firewall configured: `ufw allow 22,80,443`

### CORS

The backend currently allows `localhost:3000`. In production, restrict to your actual domain in `main.py`:

```python
allow_origins=["https://chaintrace.yourdomain.com"],
```

### Rate limiting

The `RequestLoggingMiddleware` includes per-IP rate limiting backed by Redis. Default: 60 requests/minute per IP on investigation endpoints (`/trace`, `/profile`, `/cluster`). Configure via env:

```bash
RATE_LIMIT_PER_MINUTE=60
```

### Authentication

ChainTrace v1 ships without authentication (open design decision — see spec section 17). If you are exposing your instance publicly, add HTTP Basic Auth at the Caddy/Traefik layer:

```
# Caddyfile
chaintrace.yourdomain.com {
    basicauth * {
        user $2a$14$...   # bcrypt hash — generate with: caddy hash-password
    }
    reverse_proxy ...
}
```

Full account-gated auth is planned for M7.

### Report share links

Report links use UUIDv4 identifiers (128-bit random) — not guessable. Do not add sequential IDs. Optional password protection for share links is planned for M7.

### Webhook verification

Set `ALCHEMY_WEBHOOK_AUTH_TOKEN` — the backend verifies inbound webhook signatures using HMAC-SHA256. Without this, the `/monitor/hook` endpoint accepts any payload.

---

## See also

- [03-configuration.md](03-configuration.md) — all environment variables
- [07-security.md](07-security.md) — threat model and security controls
- [09-operations.md](09-operations.md) — runbook for production incidents
