from __future__ import annotations

import asyncio
import logging
from typing import Any

from strategies.filesystem.aio import run_coroutine_sync

logger = logging.getLogger(__name__)

EXECUTE_COMMAND_TIMEOUT_SECONDS = 30.0


class CommandExecutor:
    def __init__(self, workspace: Any, truncate_bytes: int) -> None:
        self._workspace = workspace
        self._truncate_bytes = truncate_bytes

    def run(self, command: str) -> dict[str, Any]:
        try:
            result = self._execute_with_timeout(command)
        except TimeoutError:
            logger.warning("execute_command timed out: %s", command[:200])
            return {
                "stdout": "",
                "stderr": f"Command timed out after {EXECUTE_COMMAND_TIMEOUT_SECONDS}s",
                "exit_code": -3,
                "truncated": False,
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("execute_command failed: %s", command[:200])
            return {"stdout": "", "stderr": str(exc), "exit_code": -1, "truncated": False}

        stdout, stdout_truncated = self._truncate(result["stdout"])
        stderr, stderr_truncated = self._truncate(result["stderr"])
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result["exit_code"],
            "truncated": stdout_truncated or stderr_truncated,
        }

    def _execute_with_timeout(self, command: str) -> dict[str, Any]:
        async def _aexec() -> dict[str, Any]:
            r = await asyncio.wait_for(
                self._workspace.execute(command),
                timeout=EXECUTE_COMMAND_TIMEOUT_SECONDS,
            )
            stdout = await r.stdout_str()
            stderr = await r.stderr_str()
            return {"stdout": stdout, "stderr": stderr, "exit_code": r.exit_code}

        return run_coroutine_sync(lambda: _aexec())

    def _truncate(self, text: str) -> tuple[str, bool]:
        encoded = text.encode("utf-8")
        if len(encoded) <= self._truncate_bytes:
            return text, False
        clipped = encoded[: self._truncate_bytes].decode("utf-8", errors="ignore")
        footer = f"\n... (truncated, {len(encoded)} bytes total)"
        return clipped + footer, True
