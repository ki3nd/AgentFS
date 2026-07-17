from strategies.filesystem.executor import CommandExecutor


class _FakeResult:
    def __init__(self, out: str, err: str, code: int):
        self._out, self._err, self.exit_code = out, err, code

    async def stdout_str(self):
        return self._out

    async def stderr_str(self):
        return self._err


class _FakeWorkspace:
    def __init__(self, result=None, raise_exc=None):
        self._result, self._raise = result, raise_exc

    async def execute(self, command):
        if self._raise:
            raise self._raise
        return self._result


def test_run_returns_stdout_and_exit_code():
    ws = _FakeWorkspace(_FakeResult("hello\n", "", 0))
    out = CommandExecutor(ws, truncate_bytes=1024).run("ls /")
    assert out == {"stdout": "hello\n", "stderr": "", "exit_code": 0, "truncated": False}


def test_run_truncates_large_stdout():
    ws = _FakeWorkspace(_FakeResult("x" * 100, "", 0))
    out = CommandExecutor(ws, truncate_bytes=10).run("cat big")
    assert out["truncated"] is True
    assert out["stdout"].startswith("xxxxxxxxxx")
    assert "truncated" in out["stdout"]


def test_run_swallows_exceptions():
    ws = _FakeWorkspace(raise_exc=RuntimeError("network down"))
    out = CommandExecutor(ws, truncate_bytes=1024).run("ls /")
    assert out["exit_code"] == -1
    assert "network down" in out["stderr"]
    assert out["stdout"] == ""
