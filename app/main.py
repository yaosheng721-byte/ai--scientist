from fastapi import FastAPI

from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_runs import router as runs_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="CV AI Scientist",
        version="0.1.0",
        description="Web-first multi-agent AI Scientist prototype.",
    )
    app.include_router(health_router)
    app.include_router(chat_router, prefix="/chat")
    app.include_router(runs_router, prefix="/runs", tags=["runs"])
    return app


app = create_app()


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "CV AI Scientist",
        "model": settings.dashscope_model,
        "status": "ok",
    }
