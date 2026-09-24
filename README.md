# Polymarket AI Agent

Read-only research and probability-estimation agent for active Polymarket events.

## MVP

- Discover active markets from Polymarket Gamma API.
- Normalize market metadata and current implied probability.
- Score markets by liquidity/volume/expiry.
- Provide a FastAPI endpoint for market discovery.
- Keep AI/research providers behind interfaces so models and search providers can be swapped later.
- No trading or order placement in MVP.

## Architecture

```
Polymarket Gamma API
        |
        v
Market Scanner -> Market Scorer -> Research/AI (next phase)
        |                         |
        v                         v
     FastAPI                 Probability Engine
        |
        v
   PostgreSQL (next phase)
```

## Run locally

1. Copy `.env.example` to `.env`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Start: `uvicorn app.main:app --reload`.
4. Open `/docs` for the API UI.

## Important

This project is initially research-only. It does not place Polymarket orders.
