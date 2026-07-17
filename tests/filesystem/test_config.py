import pytest

from strategies.filesystem.config import FilesystemConfig, parse_mounts


def test_parse_newline_pairs_preserves_order():
    raw = "hr: d1\nkb: d2"
    assert parse_mounts(raw) == {"/hr": "d1", "/kb": "d2"}


def test_parse_skips_blank_and_comments():
    raw = "\n# a comment\nhr: d1\n\n"
    assert parse_mounts(raw) == {"/hr": "d1"}


def test_parse_normalizes_slug():
    assert parse_mounts("HR Policies: d1") == {"/HR-Policies": "d1"}


def test_parse_from_dict():
    assert parse_mounts({"hr": "d1"}) == {"/hr": "d1"}


def test_missing_colon_raises():
    with pytest.raises(ValueError):
        parse_mounts("hr d1")


def test_empty_dataset_id_raises():
    with pytest.raises(ValueError):
        parse_mounts("hr:   ")


def test_duplicate_mount_raises():
    with pytest.raises(ValueError):
        parse_mounts("hr: d1\nhr: d2")


def test_config_defaults():
    cfg = FilesystemConfig(mounts={"/hr": "d1"})
    assert cfg.truncate_kb == 50
    assert cfg.expose_semantic_search is True
    assert cfg.include_workspace_tree is True
    assert cfg.slug_metadata_name == "slug"
