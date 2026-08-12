import pytest
from app.plugins.discovery import discover_plugins
from app.plugins.query import QueryPlugin, validate_sql
from app.plugins.chart import ChartPlugin, ChartInput
from app.plugins.base import PluginContext, PluginError
from app.db.database import SessionLocal


def test_plugin_discovery():
    registry = discover_plugins("app.plugins")
    plugins = registry.all()
    names = [p.name for p in plugins]

    assert "query" in names
    assert "chart" in names
    assert len(plugins) >= 2


def test_openai_tool_definitions():
    registry = discover_plugins("app.plugins")
    tools = registry.openai_tool_definitions()

    assert len(tools) >= 2
    tool_names = [t["function"]["name"] for t in tools]
    assert "query" in tool_names
    assert "chart" in tool_names


def test_sql_ast_validation_valid():
    sql = "SELECT server_id, SUM(total_messages) FROM daily_stats GROUP BY server_id LIMIT 5"
    validated = validate_sql(sql)
    assert validated == sql


def test_sql_ast_validation_drop_rejected():
    with pytest.raises(PluginError) as exc_info:
        validate_sql("DROP TABLE servers;")
    assert "Security Violation" in str(exc_info.value) or "Only SELECT queries are allowed" in str(exc_info.value)


def test_sql_ast_validation_delete_rejected():
    with pytest.raises(PluginError):
        validate_sql("DELETE FROM members WHERE user_id = '123'")


def test_sql_ast_validation_multi_statement_rejected():
    with pytest.raises(PluginError):
        validate_sql("SELECT * FROM servers; SELECT * FROM channels;")


def test_sql_ast_validation_unsupported_table_rejected():
    with pytest.raises(PluginError) as exc_info:
        validate_sql("SELECT * FROM pg_users;")
    assert "non-whitelisted tables" in str(exc_info.value)


@pytest.mark.asyncio
async def test_query_plugin_execution():
    plugin = QueryPlugin()
    async with SessionLocal() as session:
        ctx = PluginContext(request_id="test_req", session=session)
        result = await plugin.execute(
            plugin.input_schema(sql="SELECT server_id, server_name FROM servers LIMIT 3;"),
            ctx,
        )

        assert "data" in result
        assert "count" in result
        assert result["count"] > 0
        assert "server_id" in result["data"][0]


@pytest.mark.asyncio
async def test_chart_plugin_execution():
    plugin = ChartPlugin()
    data = [
        {"day": "2026-01-01", "messages": 100},
        {"day": "2026-01-02", "messages": 200},
    ]
    ctx = PluginContext(request_id="test_chart")
    result = await plugin.execute(
        ChartInput(
            chart_type="line",
            title="Daily Messages",
            x_key="day",
            y_keys=["messages"],
            data=data,
        ),
        ctx,
    )

    assert result["type"] == "line"
    assert result["title"] == "Daily Messages"
    assert len(result["data"]) == 2
