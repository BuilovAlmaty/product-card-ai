from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db import engine
from app.routers.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Приложение запускается")

    yield

    await engine.dispose()
    print("Приложение остановлено")


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)


@app.get("/")
async def root():
    return {"message": "Hello, AI Agent!"}