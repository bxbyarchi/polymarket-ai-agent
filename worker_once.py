from __future__ import annotations

import asyncio
import logging

from app.worker import MarketWorker


async def run_once() -> None:
    logging.basicConfig(level="INFO")
    worker = MarketWorker()
    try:
        summary = await worker.run_once()
        logging.getLogger(__name__).info("Worker run completed: %s", summary)
    finally:
        await worker.polymarket.close()
        await worker.research.close()


if __name__ == "__main__":
    asyncio.run(run_once())
