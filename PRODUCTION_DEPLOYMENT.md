# Production Deployment

This setup targets a Docker VPS with HTTPS, basic auth, persistent volumes, health checks, and filesystem backups.

## 1. Prepare Environment

Create a production `.env` from `.env.example` and keep it out of git.

```bash
cp .env.example .env
```

Set at minimum:

```bash
APP_DOMAIN=your-domain.example
ACME_EMAIL=you@example.com
BASIC_AUTH_USER=admin
OLLAMA_MODEL=qwen2.5:3b
```

Generate the Caddy basic-auth password hash:

```bash
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'use-a-long-random-password'
```

Put the generated hash in `.env` as `BASIC_AUTH_HASH`.
If your shell expands `$` characters while editing or exporting the value, wrap the hash in single quotes.

## 2. DNS And Firewall

Point `APP_DOMAIN` to the VPS public IP.

Open only:

```text
22/tcp   SSH
80/tcp   HTTP for ACME redirects/challenges
443/tcp  HTTPS app access
```

The Streamlit port is bound to `127.0.0.1:8501` in production compose so it is not exposed publicly.

## 3. Start The Stack

```bash
docker compose --env-file ../.env -f docker-compose.prod.yml up -d --build
```

Run this from the `docker/` directory.

Check status:

```bash
docker compose --env-file ../.env -f docker-compose.prod.yml ps
docker compose --env-file ../.env -f docker-compose.prod.yml logs -f rag-app caddy
```

## 4. Smoke Test

```bash
curl -I https://$APP_DOMAIN
docker compose --env-file ../.env -f docker-compose.prod.yml exec rag-app python scripts/healthcheck.py
```

Expected:

- HTTPS responds through Caddy.
- Browser prompts for basic auth.
- Streamlit loads after login.
- Healthcheck clearly reports Ollama/model/Chroma/data/log status.

## 5. Backups

Run from the repo root:

```bash
scripts/backup.sh
```

The backup includes:

- `database/`
- `data/documents/`
- `data/conversations/`
- `data/processed/`

Set retention and destination:

```bash
BACKUP_DIR=/srv/ict-bot-v2-backups RETENTION_DAYS=14 scripts/backup.sh
```

Restore:

```bash
scripts/restore_backup.sh /srv/ict-bot-v2-backups/ict-bot-v2-YYYYMMDDTHHMMSSZ.tar.gz
```

Stop the app before restoring to avoid Chroma writes during extraction.

## 6. Updating

```bash
git pull
cd docker
docker compose --env-file ../.env -f docker-compose.prod.yml up -d --build
docker system prune -f
```

Use `docker system prune -f` after successful deploys on small disks to remove unused layers.
