from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from app.plugins.base import Plugin, PluginContext, PluginError


class SummaryInput(BaseModel):
    title: str = Field(..., description="Title for the summary report.")
    text_content: str = Field(..., description="Text content or dataset details to generate key insights for.")


class SummaryPlugin(Plugin):
    """
    Sample plugin demonstrating zero-code-modification extensibility.
    Takes data/text and generates structured executive takeaways.
    """

    name = "summary"
    description = (
        "Generates a structured executive summary report with key insights and takeaways from dataset details. "
        "Requires title and text_content."
    )
    input_schema = SummaryInput

    async def execute(
        self,
        arguments: SummaryInput,
        context: PluginContext,
    ) -> dict[str, Any]:
        if not arguments.text_content:
            raise PluginError("Summary text content cannot be empty.", code="EMPTY_SUMMARY_TEXT", retryable=True)

        lines = [line.strip() for line in arguments.text_content.split("\n") if line.strip()]

        return {
            "title": arguments.title,
            "summary": f"Executive summary for '{arguments.title}' generated dynamically by SummaryPlugin.",
            "insights_count": len(lines),
            "content_preview": lines[:3],
            "status": "success",
        }
