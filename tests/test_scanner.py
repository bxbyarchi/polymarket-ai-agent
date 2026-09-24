from app.services.scanner import MarketScanner


def test_parse_json_field_accepts_json_string():
    result = MarketScanner._parse_json_field('["Yes", "No"]', [])
    assert result == ["Yes", "No"]


def test_parse_json_field_returns_default_for_invalid_json():
    result = MarketScanner._parse_json_field("not-json", ["fallback"])
    assert result == ["fallback"]


def test_normalize_market():
    scanner = MarketScanner()
    result = scanner._normalize_market(
        {
            "id": 123,
            "question": "Will X happen?",
            "outcomes": '["Yes", "No"]',
            "outcomePrices": '["0.63", "0.37"]',
            "clobTokenIds": '["yes-token", "no-token"]',
            "volumeNum": 10000,
            "volume24hr": 500,
            "liquidityNum": 2500,
            "active": True,
            "closed": False,
        }
    )

    assert result["id"] == "123"
    assert result["yes_probability"] == 0.63
    assert result["liquidity"] == 2500.0
    assert result["outcomes"] == ["Yes", "No"]
