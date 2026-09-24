# Polymarket AI Agent

Research-only agent for active Polymarket events. It discovers markets, normalizes market data, assigns research priority, researches the exact resolution criteria with web search, and estimates a probability independently from the market price.

## Current architecture

Polymarket Gamma API -> Market Scanner -> Research Priority Scorer -> Analyst -> Web Search + LLM -> Probability / Edge / Sources

The system does not place orders or execute trades.

## API

- GET /health — service and AI configuration status.
- GET /markets?limit=50 — active market discovery.
- GET /scan?limit=20 — active markets with a deterministic research-priority score.
- GET /analyze/{market_id} — fetch one market and run fresh AI/web research.

## Local run

1. Copy .env.example to .env.
2. Set OPENAI_API_KEY.
3. Install dependencies: pip install -r requirements.txt.
4. Start: uvicorn app.main:app --reload.
5. Open /docs.

Default AI model is gpt-5.6-luna and can be changed with OPENAI_MODEL.

## Deployment

A Dockerfile and Render configuration are included. The repository is structured so the API can be deployed independently from the future worker/database layer.

## Next build stages

1. PostgreSQL persistence for markets, snapshots, research runs, probabilities, and sources.
2. Background scanner/worker for periodic market snapshots.
3. Research orchestrator with analyst + critic passes.
4. Probability calibration and historical backtesting.
5. Paper-trading simulation only after the research/calibration layer is stable.
6. Dashboard for market history, probability changes, research evidence, and model performance.