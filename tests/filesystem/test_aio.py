import pytest

from strategies.filesystem.aio import run_coroutine_sync


def test_runs_coroutine_and_returns_value():
    async def _coro():
        return 42

    assert run_coroutine_sync(lambda: _coro()) == 42


def test_reraises_exception():
    async def _coro():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        run_coroutine_sync(lambda: _coro())
