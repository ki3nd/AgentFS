from strategies.filesystem.filesystem import AgentFilesystem, EXECUTE_COMMAND_TOOL_NAME


def _make_bare_fs() -> AgentFilesystem:
    # Bypass build(): construct directly with stubs (no mirage/network).
    fs = AgentFilesystem.__new__(AgentFilesystem)
    fs._workspace = None
    fs._executor = _StubExecutor()
    fs._mount_descriptions = {"/docs": "HR docs"}
    fs._workspace_tree = "/\n└── docs/"
    fs._expose_semantic_search = True
    return fs


class _StubExecutor:
    def run(self, command):
        return {"stdout": f"ran:{command}", "stderr": "", "exit_code": 0, "truncated": False}


def test_tool_entity_shape():
    entity = _make_bare_fs().tool_entity()
    assert entity.identity.name == EXECUTE_COMMAND_TOOL_NAME
    assert [p.name for p in entity.parameters] == ["command"]


def test_execute_delegates_to_executor():
    assert _make_bare_fs().execute("ls /")["stdout"] == "ran:ls /"


def test_instructions_contains_mount_and_tree():
    out = _make_bare_fs().instructions()
    assert "/docs: HR docs" in out
    assert "docs/" in out
