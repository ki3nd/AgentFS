from __future__ import annotations

import asyncio
import logging
from typing import Any

from dify_plugin.entities import I18nObject
from dify_plugin.entities.tool import (
    ToolDescription,
    ToolParameter,
)
from dify_plugin.interfaces.agent import AgentToolIdentity, ToolEntity
from mirage import MountMode, Workspace
from mirage.resource.dify import DifyConfig, DifyResource

from strategies.filesystem.aio import run_coroutine_sync
from strategies.filesystem.client import DatasetMetadataClient
from strategies.filesystem.config import FilesystemConfig
from strategies.filesystem.executor import CommandExecutor
from strategies.filesystem.prompt import build_instructions
from strategies.filesystem.tree import (
    EXCLUDED_TOP_LEVEL,
    TREE_MAX_CHARS,
    TREE_MAX_DEPTH,
    render_workspace_tree,
)

logger = logging.getLogger(__name__)

EXECUTE_COMMAND_TOOL_NAME = "execute_command"
TREE_BUILD_TIMEOUT_SECONDS = 10.0

_LLM_DESCRIPTION = (
    "Run a shell command against the mounted read-only virtual knowledge "
    "filesystem. Returns JSON {stdout, stderr, exit_code, truncated}. "
    "Available commands: ls, cat, head, tail, grep, find, wc, search, awk, cut, "
    "rg, sed, sort, stat, tree, uniq. All files are plain text. "
    "Commands other than those listed are not supported."
)


class AgentFilesystem:
    def __init__(self) -> None:
        self._workspace: Workspace | None = None
        self._executor: CommandExecutor | None = None
        self._mount_descriptions: dict[str, str] = {}
        self._workspace_tree: str | None = None
        self._expose_semantic_search: bool = True

    @classmethod
    def build(
        cls, config: FilesystemConfig, base_url: str, api_key: str
    ) -> "AgentFilesystem":
        self = cls()
        self._expose_semantic_search = config.expose_semantic_search

        metadata_client = DatasetMetadataClient(base_url, api_key)

        resources: dict[str, DifyResource] = {}
        for mount_path, ds_id in config.mounts.items():
            resources[mount_path] = DifyResource(
                config=DifyConfig(
                    api_key=api_key,
                    base_url=base_url,
                    dataset_id=ds_id,
                    slug_metadata_name=config.slug_metadata_name,
                )
            )
            # description is best-effort, only used to enrich the system prompt
            self._mount_descriptions[mount_path] = metadata_client.get(ds_id)["description"]

        self._workspace = Workspace(resources, mode=MountMode.READ)
        self._executor = CommandExecutor(
            self._workspace, truncate_bytes=config.truncate_kb * 1024
        )

        if config.include_workspace_tree:
            try:
                self._workspace_tree = self._build_tree() or None
            except Exception:  # noqa: BLE001
                logger.warning("workspace tree build failed", exc_info=True)
                self._workspace_tree = None
        return self

    def _build_tree(self) -> str:
        assert self._workspace is not None

        async def _aexec() -> list[str]:
            result = await asyncio.wait_for(
                self._workspace.execute(f"find / -maxdepth {TREE_MAX_DEPTH}"),
                timeout=TREE_BUILD_TIMEOUT_SECONDS,
            )
            stdout = await result.stdout_str()
            return stdout.splitlines()

        paths = run_coroutine_sync(lambda: _aexec())
        return render_workspace_tree(
            paths=paths,
            max_depth=TREE_MAX_DEPTH,
            excluded_top_level=EXCLUDED_TOP_LEVEL,
            max_chars=TREE_MAX_CHARS,
        )

    def tool_entity(self) -> ToolEntity:
        return ToolEntity(
            identity=AgentToolIdentity(
                author="ki3nd",
                name=EXECUTE_COMMAND_TOOL_NAME,
                label=I18nObject(en_US="Execute Shell Command"),
                provider=EXECUTE_COMMAND_TOOL_NAME,
            ),
            description=ToolDescription(
                human=I18nObject(en_US="Run a shell command against mounted knowledge."),
                llm=_LLM_DESCRIPTION,
            ),
            parameters=[
                ToolParameter(
                    name="command",
                    label=I18nObject(en_US="Command"),
                    human_description=I18nObject(en_US="Shell command to run."),
                    type=ToolParameter.ToolParameterType.STRING,
                    form=ToolParameter.ToolParameterForm.LLM,
                    llm_description="Full shell command to run against the knowledge filesystem.",
                    required=True,
                ),
            ],
        )

    def execute(self, command: str) -> dict[str, Any]:
        assert self._executor is not None, "AgentFilesystem not built"
        return self._executor.run(command)

    def instructions(self) -> str:
        return build_instructions(
            self._mount_descriptions, self._workspace_tree, self._expose_semantic_search
        )

    def close(self) -> None:
        if self._workspace is not None:
            try:
                run_coroutine_sync(lambda: self._workspace.close())
            except Exception:  # noqa: BLE001
                logger.warning("workspace close failed", exc_info=True)
        self._workspace = None
        self._executor = None
        self._mount_descriptions.clear()
        self._workspace_tree = None
