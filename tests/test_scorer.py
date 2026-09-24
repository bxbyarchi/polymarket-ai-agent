from app.services.scorer import MarketScorer


def test_scorer_returns_bounded_value():
    scorer = MarketScorer()
    value = scorer.score(
        {
            "liquidity": 1_000_000,
            "volume_24h": 1_000_000,
            "volume": 10_000_000,
            "end_date": "2099-01-01T00:00:00Z",
        }
    )
    assert 0 <= value <= 1
