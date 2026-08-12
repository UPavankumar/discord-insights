from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from app.plugins.base import Plugin, PluginContext, PluginError
from app.plugins.query import QueryPlugin, QueryInput


class ChartInput(BaseModel):
    chart_type: Literal["line", "bar", "pie"] = Field(
        ...,
        description="Type of chart to generate: 'line' for time-series, 'bar' for top-N/comparisons, 'pie' for distributions.",
    )
    title: str = Field(..., description="Title for the visual chart.")
    x_key: str = Field(..., description="Column name to use for X axis / category labels.")
    y_keys: list[str] = Field(..., description="Column names to use for Y axis numeric values.")
    sql: str | None = Field(
        default=None,
        description="Optional SQL query to execute to fetch dataset rows if data parameter is omitted.",
    )
    data: list[dict[str, Any]] = Field(
        default=[],
        description="Data rows to chart. If omitted, pass sql parameter or use result from preceding query plugin.",
    )


class ChartPlugin(Plugin):
    """
    Plugin for taking structured query result data (or executing an internal SQL query)
    and formatting it into an interactive chart spec for the frontend.
    """

    name = "chart"
    description = (
        "Generates an interactive visual chart specification (line, bar, or pie chart). "
        "Can take existing data rows OR execute a SQL query directly via the 'sql' argument. "
        "Requires chart_type, title, x_key, and y_keys."
    )
    input_schema = ChartInput

    async def execute(
        self,
        arguments: ChartInput,
        context: PluginContext,
    ) -> dict[str, Any]:
        data = arguments.data

        # 1. If data is empty but sql argument is provided, execute QueryPlugin
        if not data and arguments.sql and context.session:
            query_plugin = QueryPlugin()
            query_res = await query_plugin.execute(QueryInput(sql=arguments.sql), context)
            data = query_res.get("data", [])

        # 2. Fallback to query result stored in context metadata
        if not data and "last_query_result" in context.metadata:
            data = context.metadata["last_query_result"].get("data", [])

        # 3. Fallback: query default top channels if still empty
        if not data and context.session:
            query_plugin = QueryPlugin()
            default_sql = (
                "SELECT c.channel_name, SUM(cds.message_count) AS total_messages "
                "FROM channel_daily_stats cds JOIN channels c ON cds.channel_id = c.channel_id "
                "GROUP BY c.channel_name ORDER BY total_messages DESC LIMIT 5;"
            )
            query_res = await query_plugin.execute(QueryInput(sql=default_sql), context)
            data = query_res.get("data", [])

        if not data:
            raise PluginError(
                "No data available to generate chart.",
                code="NO_DATA_FOR_CHART",
                retryable=True,
            )

        # Infer x_key / y_keys if LLM passed invalid or generic keys
        sample = data[0]
        keys = list(sample.keys())

        x_key = arguments.x_key if arguments.x_key in sample else keys[0]
        y_keys = [y for y in arguments.y_keys if y in sample]
        if not y_keys:
            # Pick first numeric or non-x key
            y_keys = [k for k in keys if k != x_key][:1]
            if not y_keys:
                y_keys = [keys[0]]

        chart_spec = {
            "type": arguments.chart_type,
            "title": arguments.title,
            "x_key": x_key,
            "y_keys": y_keys,
            "data": data,
        }

        context.metadata["last_chart_spec"] = chart_spec
        return chart_spec
