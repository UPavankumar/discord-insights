from __future__ import annotations

from typing import Any

import sqlglot
from sqlglot import exp
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, Field, model_validator
from app.plugins.base import Plugin, PluginContext, PluginError



ALLOWED_TABLES = {
    "servers",
    "channels",
    "members",
    "daily_stats",
    "channel_daily_stats",
    "messages",
}

MAX_ROW_LIMIT = 500
STATEMENT_TIMEOUT_MS = 5000


class QueryInput(BaseModel):
    sql: str = Field(
        ...,
        description="Single PostgreSQL SELECT query to execute against the Discord analytics dataset.",
    )

    @model_validator(mode="before")
    @classmethod
    def alias_query_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "sql" not in data or not data["sql"]:
                for alt_key in ["query", "sql_query", "statement"]:
                    if alt_key in data and data[alt_key]:
                        data["sql"] = data[alt_key]
                        break
        return data



def validate_sql(sql: str) -> str:
    sql = sql.strip()

    if not sql:
        raise PluginError("SQL query cannot be empty.", code="EMPTY_SQL", retryable=True)

    if ";" in sql.rstrip(";"):
        raise PluginError(
            "Multiple SQL statements separated by semicolons are strictly forbidden.",
            code="MULTI_STATEMENT_FORBIDDEN",
            retryable=True,
        )

    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception as exc:
        raise PluginError(f"SQL Syntax Error: {exc}", code="SQL_SYNTAX_ERROR", retryable=True) from exc

    if len(statements) != 1:
        raise PluginError("Exactly one SQL statement is required.", code="SINGLE_STATEMENT_REQUIRED", retryable=True)

    statement = statements[0]

    if not isinstance(statement, exp.Select):
        raise PluginError(
            f"Security Violation: Only SELECT queries are allowed (found '{type(statement).__name__}').",
            code="NON_SELECT_FORBIDDEN",
            retryable=False,
        )

    tables = {table.name.lower() for table in statement.find_all(exp.Table)}
    unknown_tables = tables - ALLOWED_TABLES

    if unknown_tables:
        raise PluginError(
            f"Access Denied: Query references non-whitelisted tables: {sorted(unknown_tables)}.",
            code="UNSUPPORTED_TABLE",
            retryable=True,
        )

    return sql


class QueryPlugin(Plugin):
    """
    Plugin for safely executing read-only SQL queries with AST validation,
    row limits, and statement timeouts.
    """

    name = "query"
    description = (
        "Executes a read-only SQL query against the Discord analytics PostgreSQL database. "
        "Allowed tables: servers, channels, members, daily_stats, channel_daily_stats, messages. "
        "Only single SELECT statements are permitted."
    )
    input_schema = QueryInput

    async def execute(
        self,
        arguments: QueryInput,
        context: PluginContext,
    ) -> dict[str, Any]:
        if not context.session:
            raise PluginError(
                "Database session missing from context.",
                code="SESSION_MISSING",
                retryable=False,
            )

        validated_sql = validate_sql(arguments.sql)

        try:
            session: AsyncSession = context.session
            
            # Set local statement timeout for security
            await session.execute(text(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT_MS}ms';"))

            try:
                result = await session.execute(text(validated_sql))
            except Exception as db_err:
                err_str = str(db_err).lower()
                if "does not exist" in err_str or "undefinedtable" in err_str:
                    import asyncio
                    from scripts.load_data import main as load_data_main
                    await asyncio.to_thread(load_data_main)
                    await session.execute(text(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT_MS}ms';"))
                    result = await session.execute(text(validated_sql))
                else:
                    raise db_err

            mappings = result.mappings().all()

            columns = list(result.keys()) if hasattr(result, "keys") else []
            rows = [dict(r) for r in mappings[:MAX_ROW_LIMIT]]

            return {
                "sql": validated_sql,
                "columns": columns,
                "data": rows,
                "count": len(rows),
                "truncated": len(mappings) > MAX_ROW_LIMIT,
            }

        except Exception as exc:
            if isinstance(exc, PluginError):
                raise exc
            raise PluginError(
                f"Database Execution Error: {exc}",
                code="DATABASE_EXECUTION_ERROR",
                retryable=True,
            ) from exc


async def execute_query(
    session: AsyncSession,
    sql: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Legacy helper function for backwards compatibility."""
    plugin = QueryPlugin()
    ctx = PluginContext(request_id="legacy", session=session)
    return await plugin.execute(QueryInput(sql=sql), ctx)
