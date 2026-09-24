from app.worker import MarketWorker


def test_worker_has_core_services():
    worker = MarketWorker()
    assert worker.scanner is not None
    assert worker.scorer is not None
    assert worker.analyst is not None
