from app.services.calibration import resolved_outcome, score_prediction, summarize


def test_resolved_outcome():
    assert resolved_outcome({"outcome_prices": ["1", "0"]}) == 1
    assert resolved_outcome({"outcome_prices": ["0", "1"]}) == 0
    assert resolved_outcome({"outcome_prices": ["0.5", "0.5"]}) is None


def test_score_prediction():
    score = score_prediction(0.8, 1)
    assert score["brier_score"] == 0.04
    assert score["log_loss"] > 0


def test_summarize_empty():
    assert summarize([])["resolved_predictions"] == 0
