from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        default_model: str = "gpt-4o-mini",
    ) -> None:
        self.api_key = api_key
        self.model = os.getenv("LLM_MODEL") or default_model
        kwargs: dict[str, Any] = {"api_key": self.api_key}

        if base_url:
            kwargs["base_url"] = base_url
        self.client = AsyncOpenAI(**kwargs)

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0].message

        tool_calls_list = []
        if choice.tool_calls:
            for tc in choice.tool_calls:
                tool_calls_list.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })

        return {
            "role": "assistant",
            "content": choice.content,
            "tool_calls": tool_calls_list if tool_calls_list else None,
        }


class FallbackNLProvider(BaseLLMProvider):
    """
    Deterministic rule-based provider for evaluation & offline testing when no LLM API key is provided.
    """

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "").lower().strip()
                break

        last_msg = messages[-1] if messages else {}

        if last_msg.get("role") == "tool" and last_msg.get("name") == "query":
            if any(term in user_msg for term in ["chart", "plot", "graph", "visualize"]):
                return {
                    "role": "assistant",
                    "content": "Generating visual chart specification from query results.",
                    "tool_calls": [
                        {
                            "id": "call_chart_1",
                            "name": "chart",
                            "arguments": {
                                "chart_type": "bar",
                                "title": "Discord Server Activity",
                                "x_key": "server_name" if "server_name" in str(last_msg.get("content")) else "day_of_week",
                                "y_keys": ["total_messages"] if "total_messages" in str(last_msg.get("content")) else ["approximate_member_count"],
                            },
                        }
                    ],
                }
            return {
                "role": "assistant",
                "content": "I have executed the SQL query against the Discord dataset and returned the structured result set above.",
                "tool_calls": None,
            }

        if last_msg.get("role") == "tool":
            return {
                "role": "assistant",
                "content": "The requested visual chart has been rendered above.",
                "tool_calls": None,
            }

        if any(term in user_msg for term in ["connected to ai", "are you ai", "who are you", "what can you do"]):
            return {
                "role": "assistant",
                "content": "Yes! I am the Exaqube Discord Analytics AI Agent. I use FastAPI, PostgreSQL, and a dynamic plugin architecture. When a free Groq or Gemini API key is supplied, I write custom SQL and generate charts using Llama 3.3 or Gemini models.",
                "tool_calls": None,
            }

        if any(term in user_msg for term in ["weather", "stock", "bitcoin", "crypto", "football", "president"]):
            return {
                "role": "assistant",
                "content": "I cannot answer that question from this dataset. I can only answer questions related to Discord servers, channels, members, daily stats, and message activity.",
                "tool_calls": None,
            }

        if any(term in user_msg for term in ["sunday", "monday", "weekday", "weekend", "day of week"]):
            sql = (
                "SELECT day_of_week, SUM(total_messages) AS total_messages "
                "FROM daily_stats "
                "GROUP BY day_of_week ORDER BY day_of_week;"
            )
            return {
                "role": "assistant",
                "content": "Querying daily message activity grouped by day of the week (0 = Sunday, 1 = Monday).",
                "tool_calls": [
                    {
                        "id": "call_day_of_week",
                        "name": "query",
                        "arguments": {"sql": sql},
                    }
                ],
            }

        if any(term in user_msg for term in ["channel", "messages per channel", "active channels"]):
            sql = (
                "SELECT c.channel_name, SUM(cds.message_count) AS total_messages "
                "FROM channel_daily_stats cds JOIN channels c ON cds.channel_id = c.channel_id "
                "GROUP BY c.channel_name ORDER BY total_messages DESC LIMIT 10;"
            )
            return {
                "role": "assistant",
                "content": "Querying top channels by total message volume.",
                "tool_calls": [
                    {
                        "id": "call_channels",
                        "name": "query",
                        "arguments": {"sql": sql},
                    }
                ],
            }

        sql = (
            "SELECT server_name, approximate_member_count "
            "FROM servers ORDER BY approximate_member_count DESC LIMIT 5;"
        )
        return {
            "role": "assistant",
            "content": "Executing query over server metrics.",
            "tool_calls": [
                {
                    "id": "call_default",
                    "name": "query",
                    "arguments": {"sql": sql},
                }
            ],
        }


class SmartFallbackProvider(BaseLLMProvider):
    """
    Tries primary providers (e.g., Groq) and automatically falls back to secondary 
    providers (Gemini, OpenAI, or FallbackNLProvider) if a rate limit (429) or error occurs.
    Emits failover status notice ONCE per provider transition.
    """

    def __init__(self, providers: list[BaseLLMProvider]) -> None:
        self.providers = [p for p in providers if p is not None]
        self.model = getattr(self.providers[0], "model", "smart_fallback") if self.providers else "fallback"
        self.last_fallback_notice: str | None = None
        self.last_emitted_notice: str | None = None

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.last_fallback_notice = None
        for idx, provider in enumerate(self.providers):
            try:
                res = await provider.chat_completion(messages, tools=tools)
                if idx > 0:
                    model_name = getattr(provider, "model", provider.__class__.__name__)
                    notice = f"⚡ Primary API limit reached. Switched to {model_name}."
                    if notice != self.last_emitted_notice:
                        self.last_fallback_notice = notice
                        self.last_emitted_notice = notice
                return res
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning(
                    "LLM Provider %s failed (%s). Falling back to next provider...",
                    provider.__class__.__name__,
                    exc,
                )
                continue

        # If all primary providers fail, use deterministic fallback provider
        fallback = FallbackNLProvider()
        notice = "⚠️ Free API quotas exhausted. Using offline deterministic engine."
        if notice != self.last_emitted_notice:
            self.last_fallback_notice = notice
            self.last_emitted_notice = notice
        return await fallback.chat_completion(messages, tools=tools)




def get_llm_provider() -> BaseLLMProvider:
    providers: list[BaseLLMProvider] = []

    # 1. Check Groq (100% Free API key)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key.strip():
        providers.append(
            OpenAICompatibleProvider(
                api_key=groq_key.strip(),
                base_url="https://api.groq.com/openai/v1",
                default_model="llama-3.3-70b-versatile",
            )
        )

    # 2. Check Google Gemini (100% Free API key)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key.strip():
        providers.append(
            OpenAICompatibleProvider(
                api_key=gemini_key.strip(),
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                default_model="gemini-2.5-flash",
            )

        )

    # 3. Check OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key.strip():
        providers.append(
            OpenAICompatibleProvider(
                api_key=openai_key.strip(),
                default_model="gpt-4o-mini",
            )
        )

    # Always append FallbackNLProvider at the end
    providers.append(FallbackNLProvider())

    if len(providers) == 1:
        return providers[0]

    return SmartFallbackProvider(providers)

