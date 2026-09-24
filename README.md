# Polymarket AI Agent

Research-only agent for active Polymarket events. It discovers markets, normalizes market data, assigns research priority, researches the exact resolution criteria with web search, estimates a probability independently from the market price, and stores market/research history.

## Current architecture

Polymarket Gamma API -> Market Scanner -> Research Priority Scorer -> PostgreSQL/SQLite persistence -> Analyst -> Web Search + LLM

The system does not place orders or execute trades.

## API

- GET /health — service, AI, and database configuration status.
- GET /markets?limit=50 — active market discovery.
- GET /scan?limit=20 — active markets with a deterministic research-priority score and a persisted snapshot.
- GET /analyze/{market_id} — fetch one market, run fresh AI/web research, and persist the research run plus sources.
- GET /history/{market_id} — return stored market snapshots and research runs.

## Persistence

The MVP now has four tables:

- markets — stable market metadata.
- market_snapshots — point-in-time price, volume, liquidity, and research-priority observations.
- research_runs — every AI probability estimate, confidence, edge, summary, and raw result.
- research_sources — URLs attached to each research run.

Local development defaults to SQLite. Set DATABASE_URL to a Render PostgreSQL connection string for production.

## Local run

1. Copy .env.example to .env.
2. Set OPENAI_API_KEY if you want /analyze.
3. Install dependencies: pip install -r requirements.txt.
4. Start: uvicorn app.main:app --reload.
5. Open /docs.

Default AI model is gpt-5.6-luna and can be changed with OPENAI_MODEL.

## Deployment

A Dockerfile and Render configuration are included. The API can run with SQLite for a simple MVP, but production history should use Render Postgres through DATABASE_URL.

## Background worker

Run `python worker.py` to start a long-running worker. By default it runs every 15 minutes, stores market snapshots, and researches up to 3 highest-priority markets per cycle. Configure `WORKER_INTERVAL_SECONDS` and `WORKER_MAX_RESEARCH_PER_CYCLE` in `.env`.

## Next build stages

1. Research orchestrator with analyst + critic passes.
2. Probability calibration and historical backtesting.
3. Paper-trading simulation only after the research/calibration layer is stable.
4. Dashboard for market history, probability changes, research evidence, and model performance.
