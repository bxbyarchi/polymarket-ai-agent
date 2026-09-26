from app.worker import MarketWorker


def test_worker_has_core_services():
    worker = MarketWorker()
    assert worker.scanner is not None
    assert worker.scorer is not None
    assert worker.analyst is not None



def test_worker_can_skip_ai_without_key(monkeypatch):
    worker = MarketWorker()
    monkeypatch.setattr(worker.settings, "openai_api_key", "")
    assert worker.settings.openai_api_key == ""
