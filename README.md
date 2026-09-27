# Polymarket AI Agent

Research-only agent for active Polymarket markets. It discovers markets, normalizes data, assigns research priority, researches exact resolution criteria with web search, estimates an independent probability, compares it with the market probability, and stores research history.

**No orders are placed and no trades are executed.**

## Architecture

Polymarket Gamma API -> Scanner -> Priority Scorer -> Persistence -> Analyst -> Critic -> Calibration -> Research history

The project includes FastAPI, SQLite for local development, PostgreSQL/asyncpg support, a local continuous worker plus a production scheduled Cron job, analyst + critic research, leakage-safe walk-forward calibration, research-quality metrics, and a web dashboard.

## API

- GET /health — service and configuration status (does not expose secrets).
- GET /ready — readiness check; returns HTTP 503 when the database is unavailable.
- GET /dashboard — browser dashboard.
- GET /markets?limit=50 — active market discovery.
- POST /scan?limit=20 — discover, score, and persist market snapshots (GET remains as a compatibility alias).
- POST /analyze/{market_id} — run fresh AI/web research and persist the result (GET remains as a compatibility alias).
- GET /history/{market_id} — market snapshots and research runs.
- GET /metrics — system counters, quality metrics, timeline, and latest research.
- GET /calibration — leakage-safe walk-forward evaluation.
- GET /calibration/raw — historical stored-probability metrics.
- GET /calibration/apply?probability=0.7 — apply empirical calibration.
- POST /resolutions/sync — synchronize newly resolved stored markets.
- GET /resolutions — stored resolution records.
- GET /docs — OpenAPI documentation.

## Calibration

Raw and calibrated probabilities are stored separately. Walk-forward evaluation only uses a resolution when that resolution was available before the prediction was created. This prevents future-outcome leakage in historical quality metrics.

Live research may use all currently resolved history because those outcomes are legitimately available at the time of a new prediction.

## Configuration

Copy .env.example to .env. GEMINI_API_KEY is required only for AI research. The current read-only scanner and resolution flow use Polymarket's public Gamma API, so a Polymarket API key is not required yet.

Other settings include GEMINI_MODEL, AI_MAX_OUTPUT_TOKENS, DATABASE_URL, ADMIN_API_KEY, WORKER_INTERVAL_SECONDS, WORKER_MAX_RESEARCH_PER_CYCLE, MIN_RESEARCH_INTERVAL_SECONDS, RESOLUTION_CONCURRENCY, market filters, and request timeout.

Never commit .env or API keys to Git. The POST /scan, POST /analyze/{market_id}, and POST /resolutions/sync endpoints require the X-Admin-Key header matching ADMIN_API_KEY.

## Local development

    pip install -r requirements.txt
    cp .env.example .env
    uvicorn app.main:app --reload

Then open /dashboard or /docs.

Without GEMINI_API_KEY, market scanning, persistence, dashboard, resolution sync, and calibration endpoints can still be exercised. AI analysis endpoints intentionally fail with a clear configuration error.

## Background worker

Run:

    python worker.py

Each cycle synchronizes stored resolutions, discovers active markets, persists snapshots, ranks research priority, researches up to WORKER_MAX_RESEARCH_PER_CYCLE markets, persists research and source evidence, and sleeps for WORKER_INTERVAL_SECONDS.

## Deployment

Docker and Render configuration are included. Production is designed as a Render Web Service plus a scheduled Render Cron job backed by managed PostgreSQL. The Blueprint in `render.yaml` links both services to the same PostgreSQL database. The Cron runs `python worker_once.py` every 15 minutes; the web service exposes the API and dashboard. Set `GEMINI_API_KEY` when AI research is enabled and set `ADMIN_API_KEY` for protected mutating endpoints. Verify `/ready`, `/health`, and `/dashboard` after deployment. The Docker entrypoint runs Alembic migrations before the application command.

The current system remains research-only even after deployment.

## Security

Secrets are read from environment variables and are never returned by API responses. The repository ignores .env and local database files should remain outside version control.

## Development status

Completed: market discovery and normalization, priority scoring, persistence, analyst + critic pipeline, resolution tracking, calibration, leakage-safe walk-forward backtesting, metrics API, dashboard, and CI test suite.

Next: apply the Render Blueprint to the existing production service/database, verify a real scan + resolution cycle, then add the real Gemini key and run end-to-end AI research. After the research layer is validated, continue with richer market detail/history UI and paper-trading simulation only.


### Database migrations

Production deployments use Alembic migrations. The Docker entrypoint runs `alembic upgrade head` before starting the API or a one-shot Cron worker.

For a persistent deployment, set `DATABASE_URL` to the same managed PostgreSQL database in both the web service and scheduled Cron worker. Do not use the default SQLite database for a multi-service production deployment: web and worker containers do not share a durable SQLite file. The repository keeps SQLite only as the convenient local default.

