from __future__ import annotations

import json
import logging

from typing import AsyncGenerator, Any, Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.providers import get_llm_provider, BaseLLMProvider
from app.plugins.discovery import discover_plugins
from app.plugins.base import PluginContext, PluginError
from app.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Discord Analytics AI Assistant.
You have access to a PostgreSQL database containing synthetic Discord activity dataset.

DATABASE SCHEMA & METADATA:
- Dataset Date Range: 2025-12-18 to 2026-06-16. (Do NOT use NOW() or CURRENT_DATE; query within 2025-12-18 to 2026-06-16).
- servers (server_id PK, server_name, owner_id, creation_date, region, verification_level, default_message_notifications, explicit_content_filter, system_channel_id, afk_channel_id, afk_timeout, widget_enabled, premium_tier, premium_subscription_count, approximate_member_count, approximate_presence_count)
- channels (channel_id PK, server_id FK, channel_name, channel_type, topic, nsfw, rate_limit_per_user, position)
- members (user_id, server_id FK, username, display_name, discriminator, avatar_hash, is_bot, join_date, last_active, roles, messages_sent, voice_minutes, is_owner)
- daily_stats (server_id FK, date PK, total_messages, new_members, active_members, total_members, day_of_week, is_weekend)
- channel_daily_stats (channel_id FK, server_id FK, date PK, message_count, active_users)
- messages (message_id PK, server_id FK, channel_id FK, user_id FK, timestamp, content, has_attachment, has_embed, reaction_count, is_pinned, length)

RULES:
1. Generate valid single-statement PostgreSQL SELECT queries using the 'query' tool.
2. When the user requests a chart/graph/visualization:
   - STEP 1: Call the 'query' tool to retrieve relevant data rows.
   - STEP 2: Call the 'chart' tool with 'chart_type' ('line', 'bar', or 'pie'), 'title', 'x_key', and 'y_keys' passing the retrieved data.
3. If asked about information outside this dataset (e.g. weather, stocks), politely decline.
4. If a query returns zero rows due to date filters, adjust the dates to match the dataset range (2025-12-18 to 2026-06-16) and retry.
"""



class AgentOrchestrator:
    def __init__(self, registry: PluginRegistry | None = None, provider: BaseLLMProvider | None = None) -> None:
        self.registry = registry or discover_plugins("app.plugins")
        self.provider = provider or get_llm_provider()

    async def run_stream(
        self,
        session: AsyncSession,
        user_request: str,
        enabled_plugins: list[str] | None = None,
        show_tip: bool = True,
        max_turns: int = 5,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Run agent orchestrator loop, yielding structured SSE event stages in real time:
        - stage: reasoning
        - stage: tool_call
        - stage: tool_progress
        - stage: result
        - stage: prose
        - stage: error
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_request},
        ]

        ctx = PluginContext(request_id="stream_req", session=session)
        all_tools = self.registry.openai_tool_definitions()
        if enabled_plugins is not None:
            tools = [t for t in all_tools if t["function"]["name"] in enabled_plugins]
            if not tools:
                tools = all_tools
        else:
            tools = all_tools



        yield {
            "stage": "reasoning",
            "payload": {"text": f"Analyzing request: '{user_request}'"},
        }

        attempts = 0
        for turn in range(max_turns):
            attempts += 1
            response = await self.provider.chat_completion(messages, tools=tools)

            if hasattr(self.provider, "last_fallback_notice") and self.provider.last_fallback_notice:
                yield {
                    "stage": "tool_progress",
                    "payload": {"status": self.provider.last_fallback_notice},
                }

            content = response.get("content")
            tool_calls = response.get("tool_calls")


            if content and not tool_calls:
                all_plugin_names = set(self.registry._plugins.keys())
                enabled_names = set([t["function"]["name"] for t in tools])
                unselected_names = all_plugin_names - enabled_names

                tip = ""
                if show_tip and unselected_names:
                    tips = []
                    if "chart" in unselected_names:
                        tips.append("enable the **'chart'** plugin in the Plugin Manager to generate visual line/bar/pie charts")
                    if "query" in unselected_names:
                        tips.append("enable the **'query'** plugin to run dynamic read-only SQL queries")
                    if "summary" in unselected_names:
                        tips.append("enable the **'summary'** plugin to generate executive summaries")
                    if tips:
                        tip = f"\n\n💡 *Tip: You can {' and '.join(tips)}.*"

                yield {
                    "stage": "prose",
                    "payload": {"text": content + tip},
                }
                return



            if tool_calls:
                openai_formatted_calls = [
                    {
                        "id": tc.get("id", "call_1"),
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]) if isinstance(tc["arguments"], dict) else str(tc["arguments"])
                        }
                    }
                    for tc in tool_calls
                ]
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": openai_formatted_calls,
                })


                for tc in tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["arguments"]
                    tool_call_id = tc.get("id", "call_1")

                    yield {
                        "stage": "tool_call",
                        "payload": {
                            "tool": tool_name,
                            "arguments": tool_args,
                        },
                    }

                    try:
                        plugin = self.registry.get(tool_name)
                        input_model = plugin.input_schema(**tool_args)

                        yield {
                            "stage": "tool_progress",
                            "payload": {"status": f"Executing {tool_name} plugin..."},
                        }

                        result = await plugin.execute(input_model, ctx)

                        if tool_name == "query":
                            ctx.metadata["last_query_result"] = result


                        yield {
                            "stage": "result",
                            "payload": {
                                "tool": tool_name,
                                "result": result,
                            },
                        }

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": str(result),
                        })

                    except PluginError as err:
                        logger.warning("Plugin execution error: %s", err)
                        yield {
                            "stage": "tool_progress",
                            "payload": {"status": f"Error: {err.message}. Retrying..."},
                        }

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": f"Error ({err.code}): {err.message}. Please correct arguments and retry.",
                        })

                    except Exception as err:
                        logger.error("Unexpected error executing plugin: %s", err)
                        yield {
                            "stage": "error",
                            "payload": {"message": str(err)},
                        }
                        return

        # If loop exhausts
        yield {
            "stage": "prose",
            "payload": {"text": "Completed request execution."},
        }

    async def run(self, session: AsyncSession, user_request: str) -> dict[str, Any]:
        """Synchronous helper collecting all stream events into a final result dictionary."""
        events = []
        async for event in self.run_stream(session, user_request):
            events.append(event)
        return {"request": user_request, "events": events}
