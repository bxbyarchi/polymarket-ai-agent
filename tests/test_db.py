import pytest

from app.db import _first_float


def test_first_float():
    assert _first_float(["0.42", "0.58"]) == 0.42


def test_first_float_invalid():
    assert _first_float(["not-a-number"]) is None


@pytest.mark.asyncio
async def test_imports():
    # Keeps the database module import covered without requiring a live database.
    from app.db import Base

    assert Base.metadata.tables["markets"] is not None
