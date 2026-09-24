import pytest

from app.agents.orchestrator import ResearchOrchestrator


class FakeAnalyst:
    async def analyze(self, market):
        return {"probability": 0.6, "market_probability": 0.5, "edge": 0.1}


class FakeCritic:
    async def review(self, market, analysis):
        return {"approved": True, "review_probability": 0.8, "confidence": 0.9}


@pytest.mark.asyncio
async def test_orchestrator_combines_estimates():
    result = await ResearchOrchestrator(FakeAnalyst(), FakeCritic()).run({"id": "1", "question": "Test"})
    assert result["probability"] == 0.7
    assert result["edge"] == 0.2
    assert result["pipeline"] == "analyst+critic"
