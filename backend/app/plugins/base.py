from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict


class PluginError(Exception):
    """Structured error that the agent can understand and potentially retry."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "PLUGIN_ERROR",
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }


class PluginContext(BaseModel):
    """Shared execution context available to every plugin."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    request_id: str
    user_id: str | None = None
    session: Any = None
    metadata: dict[str, Any] = {}



class Plugin(ABC):
    """
    Contract every plugin must implement.

    A plugin owns:
    - its identity
    - its description
    - its LLM-facing input schema
    - its execution logic

    The agent does not need to know what the plugin actually does.
    """

    name: str
    description: str
    input_schema: type[BaseModel]

    @abstractmethod
    async def execute(
        self,
        arguments: BaseModel,
        context: PluginContext,
    ) -> Any:
        """Execute the plugin and return a structured result."""
        raise NotImplementedError