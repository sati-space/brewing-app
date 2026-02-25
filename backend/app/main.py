from fastapi import FastAPI

from app.api.ai import router as ai_router
from app.api.batches import router as batch_router
from app.api.health import router as health_router
from app.api.recipes import router as recipe_router
from app.core.config import settings
from app.core.database import Base, engine
from app import models  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    Base.metadata.create_all(bind=engine)

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(recipe_router, prefix=settings.api_prefix)
    app.include_router(batch_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)
    return app


app = create_app()
