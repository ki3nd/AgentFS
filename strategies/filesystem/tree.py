from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

TREE_MAX_DEPTH = 3
TREE_MAX_CHARS = 5000
TREE_TRUNCATION_MARKER = (
    "The filesystem layout above was truncated. Use `ls` to explore specific "
    "directories before relying on omitted paths."
)
EXCLUDED_TOP_LEVEL = frozenset({"/dev", "/.sessions"})


@dataclass
class _Node:
    children: dict[str, "_Node"] = field(default_factory=dict)
    is_dir: bool = False


def render_workspace_tree(
    paths: Iterable[str],
    *,
    max_depth: int = TREE_MAX_DEPTH,
    excluded_top_level: frozenset[str] = EXCLUDED_TOP_LEVEL,
    max_chars: int = TREE_MAX_CHARS,
) -> str:
    normalized_paths = _normalize_paths(
        paths, max_depth=max_depth, excluded_top_level=excluded_top_level
    )
    if not normalized_paths:
        return ""
    root = _build_trie(normalized_paths)
    if not root.children:
        return ""
    lines = ["/"]
    _render_children(lines, root, prefix="")
    return _truncate_output(lines, max_chars=max_chars)


def _normalize_paths(
    paths: Iterable[str], *, max_depth: int, excluded_top_level: frozenset[str]
) -> list[str]:
    normalized_paths: list[str] = []
    for raw_path in paths:
        normalized_path = _normalize_path(raw_path)
        if normalized_path is None or normalized_path == "/":
            continue
        if _is_excluded_path(normalized_path, excluded_top_level=excluded_top_level):
            continue
        if _has_hidden_segment(normalized_path):
            continue
        if _path_depth(normalized_path) > max_depth:
            continue
        normalized_paths.append(normalized_path)
    return sorted(set(normalized_paths))


def _normalize_path(path: str) -> str | None:
    stripped = path.strip()
    if not stripped or not stripped.startswith("/"):
        return None
    parts = [segment for segment in stripped.split("/") if segment]
    if not parts:
        return "/"
    return "/" + "/".join(parts)


def _is_excluded_path(path: str, *, excluded_top_level: frozenset[str]) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in excluded_top_level)


def _has_hidden_segment(path: str) -> bool:
    return any(segment.startswith(".") for segment in path.split("/")[1:])


def _path_depth(path: str) -> int:
    return len(path.split("/")) - 1


def _build_trie(paths: Iterable[str]) -> _Node:
    root = _Node(is_dir=True)
    for path in paths:
        node = root
        parts = path.split("/")[1:]
        for index, part in enumerate(parts):
            child = node.children.setdefault(part, _Node())
            if index < len(parts) - 1:
                child.is_dir = True
            node = child
    return root


def _render_children(lines: list[str], node: _Node, *, prefix: str) -> None:
    children = sorted(node.children.items())
    for index, (name, child) in enumerate(children):
        is_last = index == len(children) - 1
        connector = "└── " if is_last else "├── "
        suffix = "/" if child.is_dir or child.children else ""
        lines.append(f"{prefix}{connector}{name}{suffix}")
        next_prefix = f"{prefix}{'    ' if is_last else '│   '}"
        _render_children(lines, child, prefix=next_prefix)


def _truncate_output(lines: list[str], *, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    output = "\n".join(lines)
    if len(output) <= max_chars:
        return output
    marker_block = f"\n\n{TREE_TRUNCATION_MARKER}"
    kept_lines: list[str] = []
    for line in lines:
        candidate = "\n".join([*kept_lines, line]) + marker_block
        if len(candidate) > max_chars:
            break
        kept_lines.append(line)
    if not kept_lines:
        return TREE_TRUNCATION_MARKER[:max_chars]
    return "\n".join(kept_lines) + marker_block
