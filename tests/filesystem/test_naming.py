import pytest

from strategies.filesystem.naming import normalize_mount_path


def test_simple_slug_gets_leading_slash():
    assert normalize_mount_path("hr") == "/hr"


def test_strips_and_normalizes():
    assert normalize_mount_path("  /HR Policies/ ") == "/HR-Policies"


def test_collapses_invalid_runs():
    assert normalize_mount_path("a  b__c") == "/a-b__c"


def test_empty_raises():
    with pytest.raises(ValueError):
        normalize_mount_path("   ")
    with pytest.raises(ValueError):
        normalize_mount_path("/")
