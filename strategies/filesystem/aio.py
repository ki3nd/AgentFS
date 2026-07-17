from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable, Coroutine


def run_coroutine_sync[T](coro_factory: Callable[[], Coroutine[object, object, T]]) -> T:
    """Run an async coroutine synchronously from non-async code.

    Spawns a short-lived daemon thread with a fresh event loop, executes
    ``coro_factory()`` inside it, and returns the result (or re-raises any
    exception) on the calling thread.
    """
    result: dict[str, T] = {}
    error: dict[str, BaseException] = {}

    def _runner() -> None:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            result["value"] = loop.run_until_complete(coro_factory())
        except BaseException as exc:  # noqa: BLE001
            error["exc"] = exc
        finally:
            loop.close()

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()
    if "exc" in error:
        raise error["exc"]
    return result["value"]
