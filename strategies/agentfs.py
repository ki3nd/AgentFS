from collections.abc import Generator
from typing import Any


from dify_plugin.entities.agent import AgentInvokeMessage
from dify_plugin.interfaces.agent import AgentStrategy


class AgentfsAgentStrategy(AgentStrategy):
    def _invoke(self, parameters: dict[str, Any]) -> Generator[AgentInvokeMessage]:
        pass