from strategies.filesystem.tree import render_workspace_tree


def test_renders_nested_tree():
    out = render_workspace_tree(["/docs/a.md", "/docs/b.md", "/notes/c.md"])
    assert out.splitlines()[0] == "/"
    assert "docs/" in out
    assert "a.md" in out and "b.md" in out and "c.md" in out


def test_excludes_hidden_and_excluded_top_level():
    out = render_workspace_tree(["/.sessions/x", "/dev/y", "/docs/.hidden", "/docs/ok.md"])
    assert ".sessions" not in out
    assert "/dev" not in out
    assert ".hidden" not in out
    assert "ok.md" in out


def test_empty_paths_returns_empty_string():
    assert render_workspace_tree([]) == ""
