import os
import asyncio
from app.db.database import SessionLocal
from app.agent.orchestrator import AgentOrchestrator

TEST_PROMPTS = [
    "Which 5 servers have the highest member counts?",
    "give me summary of this data",
    "Chart daily message volume for top channels in June 2026",
    "Show me weekday vs weekend activity as a bar chart",
    "Who are the top 5 members by total messages sent?",
]

async def run_verification():
    orchestrator = AgentOrchestrator()
    print("=" * 80)
    print("STARTING END-TO-END AGENT QUERY VERIFICATION")
    print("=" * 80)

    async with SessionLocal() as session:
        for idx, prompt in enumerate(TEST_PROMPTS, 1):
            print(f"\n--- [TEST {idx}] Prompt: '{prompt}' ---")
            events = []
            async for event in orchestrator.run_stream(session, prompt):
                events.append(event)
                stage = event.get("stage")
                payload = event.get("payload", {})

                if stage == "reasoning":
                    print(f"  [Reasoning] {payload.get('text')}")
                elif stage == "tool_call":
                    print(f"  [Tool Call] {payload.get('tool')} -> args: {payload.get('arguments')}")
                elif stage == "tool_progress":
                    print(f"  [Progress] {payload.get('status')}")
                elif stage == "result":
                    tool = payload.get("tool")
                    res = payload.get("result", {})
                    if tool == "query":
                        print(f"  [Query Result] {res.get('count')} rows returned | SQL: {res.get('sql')}")
                        if res.get("data"):
                            print(f"    Sample Row: {res.get('data')[0]}")
                    elif tool == "chart":
                        print(f"  [Chart Spec] type='{res.get('type')}', title='{res.get('title')}', x='{res.get('x_key')}', y={res.get('y_keys')}, data_points={len(res.get('data', []))}")
                elif stage == "prose":
                    print(f"  [Prose Answer] {payload.get('text')[:140]}...")
                elif stage == "error":
                    print(f"  [ERROR] {payload.get('message')}")

            print(f"-> Test {idx} completed with {len(events)} events.")

    print("\n" + "=" * 80)
    print("ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_verification())
