# Render production setup

The repository contains a Render Blueprint in render.yaml.

## Target resources

- Web service: polymarket-ai-agent
- Background worker: polymarket-ai-agent-worker
- PostgreSQL: polymarket-ai-agent-db
- Web health endpoint: /ready
- Worker command: python worker.py

## Plan and cost note

Render currently does not offer a Free compute plan for continuous background workers. The Blueprint therefore keeps the web service on Free, while the worker uses Render's smallest paid worker plan (0.5c-512mb). Render's current pricing lists that worker plan at $7/month. The Postgres resource remains on Free, subject to Render's current Free-tier limitations.

## Apply the Blueprint

The existing Web Service was created before the Blueprint was applied, so its current settings are not automatically replaced by render.yaml.

In Render Dashboard:

1. Open the Blueprint/service creation flow.
2. Select the GitHub repository bxbyarchi/polymarket-ai-agent.
3. Select branch main.
4. Use the repository's render.yaml.
5. Confirm the PostgreSQL resource and both services.
6. For the web service, confirm /ready is the health check.
7. Confirm DATABASE_URL is linked from polymarket-ai-agent-db.
8. Confirm the worker uses python worker.py.
9. Confirm the worker plan is 0.5c-512mb.
10. Leave OPENAI_API_KEY unset until AI research is intentionally enabled.
11. Set a strong random ADMIN_API_KEY before exposing mutation endpoints.

## Verification order

After deployment:

1. GET /ready must return HTTP 200 and {"status":"ready"}.
2. Web logs must show Alembic migrations completing before Uvicorn starts.
3. Worker logs must show recurring "Worker cycle completed".
4. PostgreSQL should contain the migration tables.
5. GET /health should report the database as reachable.
6. Only after this should OPENAI_API_KEY be added for live research.

## Important

Do not set APP_ENV=production on the current SQLite-backed service before DATABASE_URL is connected. The application intentionally fails closed rather than silently using ephemeral SQLite in production.

The system is research-only: it does not place Polymarket orders or execute trades.
