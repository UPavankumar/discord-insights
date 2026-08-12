import asyncio

from app.db.database import SessionLocal
from app.plugins.query import execute_query


async def main():
    async with SessionLocal() as session:
        result = await execute_query(
            session,
            """
            SELECT
                server_id,
                SUM(total_messages) AS total_messages
            FROM daily_stats
            GROUP BY server_id
            ORDER BY total_messages DESC
            LIMIT 5
            """,
        )

        print(result)


if __name__ == "__main__":
    asyncio.run(main())
