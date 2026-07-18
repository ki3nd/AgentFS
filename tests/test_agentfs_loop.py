"""Regression tests for the agentfs strategy loop (credential guard, tool dispatch).

These construct `AgentfsAgentStrategy` via `__new__` to bypass the SDK's
`__init__` (which requires a live `AgentRuntime`/`Session`), then stub the
minimal pieces of the SDK contract the code path under test actually touches:
`self.session.model.llm.invoke` (blocking mode) and, where relevant,
`self.session.tool.invoke`. No live Dify instance is required.
"""

from __future__ import annotations

from typing import Any

from dify_plugin.entities.agent import AgentInvokeMessage
from dify_plugin.entities.model.llm import LLMModelConfig, LLMResult, LLMUsage
from dify_plugin.entities.model.message import AssistantPromptMessage

from strategies.agentfs import AgentfsAgentStrategy


def _zero_usage() -> LLMUsage:
    return LLMUsage(
        prompt_tokens=0,
        prompt_unit_price=0,
        prompt_price_unit=0,
        prompt_price=0,
        completion_tokens=0,
        completion_unit_price=0,
        completion_price_unit=0,
        completion_price=0,
        total_tokens=0,
        total_price=0,
        currency="USD",
        latency=0,
    )


def _make_strategy() -> AgentfsAgentStrategy:
    strategy = AgentfsAgentStrategy.__new__(AgentfsAgentStrategy)
    strategy.response_type = AgentInvokeMessage
    return strategy


def _model_params(model_dict: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": "fake_provider",
        "model": "fake-model",
        "mode": "chat",
        "completion_params": {},
        "entity": None,
        "history_prompt_messages": [],
        **model_dict,
    }


def _base_parameters(**overrides: Any) -> dict[str, Any]:
    params: dict[str, Any] = {
        "query": "hello",
        "instruction": "",
        "model": _model_params({}),
        "tools": [],
        "maximum_iterations": 10,
        "context": None,
        "datasets": None,
        "expose_semantic_search": True,
        "include_workspace_tree": True,
        "truncate_kb": 50,
    }
    params.update(overrides)
    return params


def _blocking_result_with_tool_call(
    tool_call_name: str, tool_call_args: dict[str, Any] | None = None
) -> LLMResult:
    tool_call_args = tool_call_args or {}
    message = AssistantPromptMessage(
        content="",
        tool_calls=[
            AssistantPromptMessage.ToolCall(
                id="call_1",
                type="function",
                function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                    name=tool_call_name,
                    arguments="{}" if not tool_call_args else __import__("json").dumps(tool_call_args),
                ),
            )
        ],
    )
    return LLMResult(
        model="fake-model",
        prompt_messages=[],
        message=message,
        usage=_zero_usage(),
    )


def _final_result(text: str = "done") -> LLMResult:
    message = AssistantPromptMessage(content=text, tool_calls=[])
    return LLMResult(model="fake-model", prompt_messages=[], message=message, usage=_zero_usage())


class _FakeLLM:
    """Returns a queued sequence of blocking LLMResults, one per invoke() call."""

    def __init__(self, results: list[LLMResult]):
        self._results = list(results)

    def invoke(self, **kwargs: Any) -> LLMResult:
        assert self._results, "invoke() called more times than results were queued"
        return self._results.pop(0)


class _FakeModelSession:
    def __init__(self, llm: _FakeLLM):
        self.llm = llm


class _FakeToolSession:
    def __init__(self):
        self.invoke_calls: list[dict[str, Any]] = []

    def invoke(self, **kwargs: Any):
        self.invoke_calls.append(kwargs)
        return iter(())


class _FakeSession:
    def __init__(self, llm: _FakeLLM):
        self.model = _FakeModelSession(llm)
        self.tool = _FakeToolSession()


class _FakeAgentFilesystem:
    """Stand-in for strategies.filesystem.AgentFilesystem."""

    def __init__(self):
        self.executed_commands: list[str] = []
        self.closed = False

    def instructions(self) -> str:
        return "fake fs instructions"

    def tool_entity(self):
        from dify_plugin.entities import I18nObject
        from dify_plugin.entities.tool import ToolDescription
        from dify_plugin.interfaces.agent import AgentToolIdentity, ToolEntity
        from strategies.filesystem import EXECUTE_COMMAND_TOOL_NAME

        return ToolEntity(
            identity=AgentToolIdentity(
                author="ki3nd",
                name=EXECUTE_COMMAND_TOOL_NAME,
                label=I18nObject(en_US="Execute Shell Command"),
                provider=EXECUTE_COMMAND_TOOL_NAME,
            ),
            description=ToolDescription(
                human=I18nObject(en_US="test"), llm="test"
            ),
            parameters=[],
        )

    def execute(self, command: str) -> dict[str, Any]:
        self.executed_commands.append(command)
        return {"stdout": "ok", "stderr": "", "exit_code": 0, "truncated": False}

    def close(self) -> None:
        self.closed = True


def test_missing_credentials_yields_error_and_returns(monkeypatch):
    """(a) mounts present but blank base_url/api_key -> error message, no fs built."""
    strategy = _make_strategy()
    strategy.session = _FakeSession(_FakeLLM([]))

    build_called = {"count": 0}

    def _fail_build(*args, **kwargs):
        build_called["count"] += 1
        raise AssertionError("AgentFilesystem.build should not be called")

    monkeypatch.setattr(
        "strategies.agentfs.AgentFilesystem.build", staticmethod(_fail_build)
    )

    parameters = _base_parameters(
        datasets="hr: ds123",
        knowledge_base_url="",
        knowledge_api_key="",
    )

    messages = list(strategy._invoke(parameters))

    assert build_called["count"] == 0
    texts = [
        m.message.text
        for m in messages
        if m.type == AgentInvokeMessage.MessageType.TEXT
    ]
    assert any(
        "knowledge_base_url" in t and "knowledge_api_key" in t for t in texts
    ), texts


def test_missing_credentials_ok_when_no_mounts():
    """No dataset mounts configured -> credential guard does not fire."""
    strategy = _make_strategy()
    strategy.session = _FakeSession(_FakeLLM([_final_result("hi")]))

    parameters = _base_parameters(
        datasets=None,
        knowledge_base_url="",
        knowledge_api_key="",
        maximum_iterations=1,
    )

    messages = list(strategy._invoke(parameters))
    texts = [
        m.message.text
        for m in messages
        if m.type == AgentInvokeMessage.MessageType.TEXT
    ]
    assert any("hi" in t for t in texts)


def test_execute_command_dispatch_routes_to_fake_fs(monkeypatch):
    """(b) a tool call named execute_command routes to fake_fs.execute(...),
    not to self.session.tool.invoke."""
    strategy = _make_strategy()

    fake_fs = _FakeAgentFilesystem()
    monkeypatch.setattr(
        "strategies.agentfs.AgentFilesystem.build",
        staticmethod(lambda *a, **kw: fake_fs),
    )

    llm = _FakeLLM(
        [
            _blocking_result_with_tool_call(
                "execute_command", {"command": "ls /hr"}
            ),
            _final_result("final answer"),
        ]
    )
    strategy.session = _FakeSession(llm)

    parameters = _base_parameters(
        datasets="hr: ds123",
        knowledge_base_url="https://dify.example/v1",
        knowledge_api_key="secret-key",
        maximum_iterations=10,
    )

    messages = list(strategy._invoke(parameters))

    assert fake_fs.executed_commands == ["ls /hr"]
    assert strategy.session.tool.invoke_calls == []
    assert fake_fs.closed is True
    texts = [
        m.message.text
        for m in messages
        if m.type == AgentInvokeMessage.MessageType.TEXT
    ]
    assert any("final answer" in t for t in texts)


def test_unknown_tool_name_does_not_raise(monkeypatch):
    """(c) a tool call with an unregistered name is handled gracefully (no KeyError)."""
    strategy = _make_strategy()

    llm = _FakeLLM(
        [
            _blocking_result_with_tool_call("totally_unknown_tool", {"x": 1}),
            _final_result("recovered"),
        ]
    )
    strategy.session = _FakeSession(llm)

    parameters = _base_parameters(
        datasets=None,
        knowledge_base_url="",
        knowledge_api_key="",
        maximum_iterations=10,
    )

    # Should not raise KeyError (or any exception) despite the unknown tool name.
    messages = list(strategy._invoke(parameters))

    texts = [
        m.message.text
        for m in messages
        if m.type == AgentInvokeMessage.MessageType.TEXT
    ]
    assert any("recovered" in t for t in texts)
