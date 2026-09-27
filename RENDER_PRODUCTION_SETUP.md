# Render production setup

The repository contains a Render Blueprint in render.yaml.

## Target resources

- Web service: polymarket-ai-agent
- Scheduled research/resolution job: polymarket-ai-agent-worker
- PostgreSQL: polymarket-ai-agent-db
- Web health endpoint: /ready
- Cron command: python worker_once.py
- Cron schedule: every 15 minutes (UTC)

## Plan and cost note

A continuously running background worker costs $7/month at Render's smallest paid compute plan. This project does not need a continuously running process: each research/resolution cycle is bounded and can run as a scheduled Cron job. Render Cron is billed by active runtime and has a $1/month minimum per Cron service. The Blueprint therefore uses the smallest Cron compute plan (0.5c-512mb), which should keep the scheduled worker materially cheaper than an always-on worker when cycles are short. citeturn1search0turn1search2

The Postgres resource remains on Free, subject to Render's current Free-tier limitations. In particular, Free Postgres expires 30 days after creation unless upgraded. citeturn1search3

## Apply the Blueprint

The existing Web Service was created before the Blueprint was applied, so its current settings are not automatically replaced by render.yaml.

In Render Dashboard:

1. Open the Blueprint/service creation flow.
2. Select the GitHub repository bxbyarchi/polymarket-ai-agent.
3. Select branch main.
4. Use the repository's render.yaml.
5. Confirm the PostgreSQL resource, web service, and Cron service.
6. For the web service, confirm /ready is the health check.
7. Confirm DATABASE_URL is linked from polymarket-ai-agent-db.
8. Confirm the scheduled job uses python worker_once.py.
9. Confirm the schedule is */15 * * * * (UTC).
10. Leave OPENAI_API_KEY unset until AI research is intentionally enabled.
11. Set a strong random ADMIN_API_KEY before exposing mutation endpoints.

## Verification order

After deployment:

1. GET /ready must return HTTP 200 and {"status":"ready"}.
2. Web logs must show Alembic migrations completing before Uvicorn starts.
3. Cron run logs must show "Worker run completed".
4. PostgreSQL should contain the migration tables.
5. GET /health should report the database as reachable.
6. Trigger one Cron run manually and confirm it exits successfully.
7. Only after this should OPENAI_API_KEY be added for live research.

## Important

Do not set APP_ENV=production on the current SQLite-backed service before DATABASE_URL is connected. The application intentionally fails closed rather than silently using ephemeral SQLite in production.

The system is research-only: it does not place Polymarket orders or execute trades.
