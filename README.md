# Polymarket AI Agent

Research-only agent for active Polymarket markets. It discovers markets, normalizes data, assigns research priority, researches exact resolution criteria with web search, estimates an independent probability, compares it with the market probability, and stores research history.

**No orders are placed and no trades are executed.**

## Architecture

Polymarket Gamma API -> Scanner -> Priority Scorer -> Persistence -> Analyst -> Critic -> Calibration -> Research history

The project includes FastAPI, SQLite for local development, PostgreSQL/asyncpg support, a background worker, analyst + critic research, leakage-safe walk-forward calibration, research-quality metrics, and a web dashboard.

## API

- GET /health — service and configuration status (does not expose secrets).
- GET /dashboard — browser dashboard.
- GET /markets?limit=50 — active market discovery.
- GET /scan?limit=20 — discover, score, and persist market snapshots.
- GET /analyze/{market_id} — run fresh AI/web research and persist the result.
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

Copy .env.example to .env. OPENAI_API_KEY is required only for AI research. The current read-only scanner and resolution flow use Polymarket's public Gamma API, so a Polymarket API key is not required yet.

Other settings include OPENAI_MODEL, AI_MAX_OUTPUT_TOKENS, DATABASE_URL, WORKER_INTERVAL_SECONDS, WORKER_MAX_RESEARCH_PER_CYCLE, market filters, and request timeout.

Never commit .env or API keys to Git.

## Local development

    pip install -r requirements.txt
    cp .env.example .env
    uvicorn app.main:app --reload

Then open /dashboard or /docs.

Without OPENAI_API_KEY, market scanning, persistence, dashboard, resolution sync, and calibration endpoints can still be exercised. AI analysis endpoints intentionally fail with a clear configuration error.

## Background worker

Run:

    python worker.py

Each cycle synchronizes stored resolutions, discovers active markets, persists snapshots, ranks research priority, researches up to WORKER_MAX_RESEARCH_PER_CYCLE markets, persists research and source evidence, and sleeps for WORKER_INTERVAL_SECONDS.

## Deployment

Docker and Render configuration are included. For production: create PostgreSQL, set DATABASE_URL, set OPENAI_API_KEY when AI research is enabled, deploy the web service, run the worker as a separate long-running process/service, and verify /health and /dashboard.

The current system remains research-only even after deployment.

## Security

Secrets are read from environment variables and are never returned by API responses. The repository ignores .env and local database files should remain outside version control.

## Development status

Completed: market discovery and normalization, priority scoring, persistence, analyst + critic pipeline, resolution tracking, calibration, leakage-safe walk-forward backtesting, metrics API, dashboard, and CI test suite.

Next: production Postgres deployment, real OpenAI key, end-to-end live research run, richer market detail/history UI, and paper-trading simulation only after the research layer is validated.


### Database migrations

Production deployments use Alembic migrations. The Docker entrypoint runs `alembic upgrade head` before starting either the API or worker.

For a persistent deployment, set `DATABASE_URL` to a managed PostgreSQL database. The repository still keeps SQLite as the convenient local default.

