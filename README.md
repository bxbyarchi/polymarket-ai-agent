# Polymarket AI Agent

A read-only AI research agent for active Polymarket markets.

## What it does now

1. Pulls active markets from the public Polymarket Gamma API.
2. Normalizes market metadata and the current YES price/probability.
3. Exposes a FastAPI API for market discovery.
4. Can analyze a specific market with an OpenAI model using live web search.
5. Returns an estimated YES probability, confidence, key factors, counter-factors, and cited source URLs.
6. Does **not** place orders.

Polymarket's Gamma API is public and read-only for market discovery; the CLOB API is used later for order-book and execution functionality. The current implementation deliberately stays read-only. citeturn1search1turn1search13

## Architecture

```
Polymarket Gamma API
        |
        v
  Market Scanner
        |
        +----> /markets
        |
        v
  Market Research
        |
        v
 OpenAI Responses API
   + web_search
        |
        v
 Probability Estimate
        |
        v
 Dashboard / database (next phase)
```

## Environment

Copy `.env.example` to `.env` and set:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-6-astra`)

The OpenAI Responses API supports built-in web search tools, which is what the first research agent uses. citeturn3search4

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Then open `/docs`.

### Endpoints

- `GET /health`
- `GET /markets?limit=50`
- `GET /analyze/{market_id}`

Example:

```
GET /markets?limit=20
GET /analyze/540817
```

## Next milestones

- PostgreSQL persistence for every market snapshot and AI forecast.
- CLOB price history and order-book features.
- Event-level grouping instead of only individual markets.
- Research/critic multi-agent pass.
- Probability calibration and Brier-score tracking.
- Backtesting / paper trading.
- Scheduled background scans.
- Dashboard.
- Real-money execution only as a separate, explicitly enabled phase.
