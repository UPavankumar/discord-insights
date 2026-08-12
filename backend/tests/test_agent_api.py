import os
os.environ["TESTING"] = "1"

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.agent.orchestrator import AgentOrchestrator
from app.db.database import SessionLocal


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "database" in data
        assert data["plugins_count"] >= 2


@pytest.mark.asyncio
async def test_agent_orchestrator_run():
    orchestrator = AgentOrchestrator()
    async with SessionLocal() as session:
        res = await orchestrator.run(session, "Show me top 5 servers by total messages")
        assert "events" in res
        events = res["events"]
        assert len(events) > 0
        stages = [e["stage"] for e in events]
        assert "reasoning" in stages
        assert "tool_call" in stages or "prose" in stages


@pytest.mark.asyncio
async def test_chat_api_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/chat", json={"message": "Show me top 5 servers"})
        assert response.status_code == 200
        data = response.json()
        assert "events" in data


@pytest.mark.asyncio
async def test_chat_stream_sse_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/chat/stream", params={"message": "Top 5 servers"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_activity_channel_day_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/activity/channel/day", params={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
