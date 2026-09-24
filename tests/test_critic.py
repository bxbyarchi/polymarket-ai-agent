from app.agents.critic import Critic


def test_parse_fenced_json_response():
    result = Critic._parse_json(
        """```
{"approved": true, "review_probability": 0.58, "confidence": 0.7}
```"""
    )
    assert result["approved"] is True


def test_clamp():
    assert Critic._clamp(1.5) == 1.0
    assert Critic._clamp(-0.1) == 0.0
