# Render production setup

The repository contains a Render Blueprint in `render.yaml`.

## Target resources

- Web service: polymarket-ai-agent
- Scheduled research/resolution job: polymarket-ai-agent-worker
- PostgreSQL: polymarket-ai-agent-db
- Web health endpoint: /ready
- Cron command: python worker_once.py
- Cron schedule: every 15 minutes (UTC)

## Current production state

The existing Web Service and Cron worker are already connected to this repository and are deploying from `main`. The production application has been observed completing scheduled worker cycles successfully.

The repository Blueprint remains the source of truth for a reproducible deployment configuration. Because the original Web Service was created before the Blueprint was applied, review the existing Render service settings before applying the Blueprint to avoid creating duplicate resources.

## Secrets

Set these only in Render's environment configuration and never commit real values:

- GEMINI_API_KEY
- ADMIN_API_KEY
- Optional POLYMARKET_API_KEY
- Optional POLYMARKET_API_SECRET
- Optional POLYMARKET_API_PASSPHRASE
- Optional POLYMARKET_ADDRESS

Google Search grounding is enabled by default because the research agent is intended to use current web information. Gemini 3.5 Flash-Lite and Gemini 3.1 Flash-Lite are currently supported stable API models.

## Verification order

1. GET /ready must return HTTP 200 and `{"status":"ready"}`.
2. Web logs should show Alembic migrations completing before Uvicorn starts.
3. Cron logs should show `Worker run completed`.
4. Verify /health reports the database as reachable.
5. Trigger or wait for one Cron run and confirm it exits successfully.
6. Run a real event research request with an authorized `X-Admin-Key` and confirm the result contains an event question, probability, evidence summary and sources.

## Database lifecycle

The current managed PostgreSQL resource is on Render's Free plan and has an expiry date. It should be upgraded to a paid plan before that expiry or replaced through a planned migration. Do not switch production back to SQLite.

## Security

Reference URLs are fetched server-side. Keep this endpoint behind `ADMIN_API_KEY` and restrict outbound access appropriately at the infrastructure layer. The system is research-only: it does not place Polymarket orders or execute trades.
