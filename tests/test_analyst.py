from app.agents.analyst import Analyst


def test_parse_json_response():
    result = Analyst._parse_json(
        '{"probability": 0.62, "confidence": 0.8, "summary": "ok"}'
    )
    assert result["probability"] == 0.62


def test_parse_fenced_json_response():
    result = Analyst._parse_json(
        """```
{"probability": 0.62}
```"""
    )
    assert result["probability"] == 0.62


def test_clamp_probability():
    assert Analyst._clamp(1.5) == 1.0
    assert Analyst._clamp(-0.2) == 0.0
