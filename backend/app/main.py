import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import router, health as health_check
from app.db.database import get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-load data schema and dataset in background thread on startup
    try:
        from scripts.load_data import main as load_data_main
        await asyncio.to_thread(load_data_main)
        print("Dataset & Schema successfully initialized on startup.")
    except Exception as err:
        print("Data auto-load notice:", err)
    yield


app = FastAPI(
    title="Exaqube Analytics API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def root_health(session: AsyncSession = Depends(get_session)):
    return await health_check(session)


app.include_router(router)
