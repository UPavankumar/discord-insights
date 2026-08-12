import asyncio

from app.agent.orchestrator import AgentOrchestrator
from app.db.database import SessionLocal


async def main():
    agent = AgentOrchestrator()

    async with SessionLocal() as session:
        result = await agent.run(
            session,
            "Show me the top 5 servers by total messages",
        )

        print(result)


if __name__ == "__main__":
    asyncio.run(main())
