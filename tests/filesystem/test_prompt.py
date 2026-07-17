from strategies.filesystem.prompt import build_instructions


def test_includes_mounts_and_tree_and_search_hint():
    out = build_instructions(
        {"/docs": "HR docs", "/kb": "Product KB"},
        workspace_tree="/\n└── docs/",
        expose_semantic_search=True,
    )
    assert "/docs: HR docs" in out
    assert "/kb: Product KB" in out
    assert "└── docs/" in out
    assert "search" in out.lower()


def test_without_search_hint_omits_search_command():
    out = build_instructions({"/docs": "HR docs"}, None, expose_semantic_search=False)
    assert "semantic retrieval" not in out.lower()
    assert "/docs: HR docs" in out


def test_empty_mounts_returns_empty():
    assert build_instructions({}, None, expose_semantic_search=True) == ""
