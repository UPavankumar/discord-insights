from __future__ import annotations

import json
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db.database import get_session
from app.agent.orchestrator import AgentOrchestrator
from app.plugins.discovery import discover_plugins


router = APIRouter(prefix="/api", tags=["analytics"])
orchestrator = AgentOrchestrator()


class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or question.")


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1;"))
        db_healthy = True
    except Exception:
        db_healthy = False

    registry = discover_plugins("app.plugins")
    plugins = [p.name for p in registry.all()]

    return {
        "status": "ok" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "plugins_count": len(plugins),
        "plugins": plugins,
    }


@router.post("/chat")
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await orchestrator.run(session, request.message)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "AGENT_ERROR", "message": str(exc)},
        ) from exc


@router.get("/chat/stream")
async def chat_stream(
    message: str = Query(..., description="User message to stream agent stages for"),
    plugins: str | None = Query(default=None, description="Comma-separated list of enabled plugin names"),
    show_tip: bool = Query(default=True, description="Whether to include unselected plugin tip in response"),
    session: AsyncSession = Depends(get_session),
):
    enabled_list = [p.strip() for p in plugins.split(",") if p.strip()] if plugins else None

    async def event_generator():
        try:
            async for stage_event in orchestrator.run_stream(session, message, enabled_plugins=enabled_list, show_tip=show_tip):


                yield {
                    "event": "message",
                    "data": json.dumps(stage_event, default=str),
                }

            yield {
                "event": "end",
                "data": json.dumps({"status": "complete"}),
            }
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"stage": "error", "payload": {"message": str(exc)}}),
            }


    return EventSourceResponse(event_generator())


@router.get("/activity/channel/day")
async def activity_per_channel_per_day(
    server_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    sql = """
        SELECT
            channel_id,
            server_id,
            date,
            message_count,
            active_users
        FROM channel_daily_stats
        WHERE (CAST(:server_id AS TEXT) IS NULL OR server_id = :server_id)
        ORDER BY date DESC, message_count DESC
        LIMIT :limit OFFSET :offset

    """

    result = await session.execute(
        text(sql),
        {"server_id": server_id, "limit": limit, "offset": offset},
    )

    rows = [dict(row) for row in result.mappings().all()]

    return {
        "data": rows,
        "count": len(rows),
        "limit": limit,
        "offset": offset,
    }


@router.get("/servers")
async def list_servers(
    limit: int = Query(default=10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    sql = """
        SELECT server_id, server_name, region, approximate_member_count
        FROM servers
        ORDER BY approximate_member_count DESC
        LIMIT :limit
    """
    result = await session.execute(text(sql), {"limit": limit})
    rows = [dict(r) for r in result.mappings().all()]
    return {"data": rows, "count": len(rows)}
