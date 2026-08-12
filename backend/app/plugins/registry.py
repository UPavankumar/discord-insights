from __future__ import annotations

from typing import Any

from .base import Plugin


class PluginRegistry:
    """
    Runtime registry of available plugins.

    The agent interacts with this registry rather than importing
    individual plugins directly.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        if plugin.name in self._plugins:
            raise ValueError(
                f"Plugin '{plugin.name}' is already registered."
            )

        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> Plugin:
        try:
            return self._plugins[name]
        except KeyError:
            raise KeyError(f"Unknown plugin: {name}")

    def all(self) -> list[Plugin]:
        return list(self._plugins.values())

    def tool_definitions(self) -> list[dict[str, Any]]:
        """
        Convert registered plugins into the tool definitions
        consumed by the agent/provider layer.
        """

        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "input_schema": plugin.input_schema.model_json_schema(),
            }
            for plugin in self._plugins.values()
        ]

    def openai_tool_definitions(self) -> list[dict[str, Any]]:
        """Format registered plugins for OpenAI function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": plugin.name,
                    "description": plugin.description,
                    "parameters": plugin.input_schema.model_json_schema(),
                },
            }
            for plugin in self._plugins.values()
        ]