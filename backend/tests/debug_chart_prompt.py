import os
import asyncio
from app.db.database import SessionLocal
from app.agent.orchestrator import AgentOrchestrator

async def main():
    orchestrator = AgentOrchestrator()
    async with SessionLocal() as session:
        async for event in orchestrator.run_stream(session, "give me summary of this data"):
            print("EVENT:", event)

if __name__ == "__main__":
    asyncio.run(main())
