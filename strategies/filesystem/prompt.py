from __future__ import annotations

_COMMANDS_WITH_SEARCH = (
    "Use shell commands via `execute_command` to inspect them: "
    "`ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `search`, `awk`, `cut`, "
    "`rg`, `sed`, `sort`, `stat`, `tree`, `uniq`. "
    "Use `search` for semantic retrieval; use `grep` for literal text. "
    "All files are treated as plain text, regardless of their original extension. "
    "Commands other than those listed above are not supported."
)
_COMMANDS_WITHOUT_SEARCH = (
    "Use shell commands via `execute_command` to inspect them: "
    "`ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `awk`, `cut`, `rg`, `sed`, "
    "`sort`, `stat`, `tree`, `uniq`. "
    "All files are treated as plain text, regardless of their original extension. "
    "Commands other than those listed above are not supported."
)


def build_instructions(
    mount_descriptions: dict[str, str],
    workspace_tree: str | None,
    expose_semantic_search: bool,
) -> str:
    if not mount_descriptions:
        return ""
    sections: list[str] = [
        "This agent has access to the following mounted datasets via a read-only "
        "virtual filesystem. Use the `execute_command` tool to run shell commands "
        "to inspect their contents."
    ]
    if workspace_tree:
        sections.append(f"Workspace layout (depth <= 3):\n{workspace_tree}")
    lines = ["Available knowledge mounts (read-only virtual filesystem):"]
    for path, desc in mount_descriptions.items():
        lines.append(f"- {path}: {desc}")
    sections.append("\n".join(lines))
    sections.append(_COMMANDS_WITH_SEARCH if expose_semantic_search else _COMMANDS_WITHOUT_SEARCH)
    return "\n\n".join(sections)
