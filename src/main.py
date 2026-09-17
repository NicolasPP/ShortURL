from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from api import database_manager, router as url_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await database_manager.close()


app: FastAPI = FastAPI(
    title="URL Shortener API",
    version="1.0.0",
    description="High-performance, production-ready URL shortener service.",
    lifespan=lifespan,
)

app.include_router(url_router, prefix="/api/v1")
