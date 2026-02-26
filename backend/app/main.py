from fastapi import FastAPI

from app import models  # noqa: F401
from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.batches import router as batch_router
from app.api.health import router as health_router
from app.api.inventory import router as inventory_router
from app.api.notifications import router as notifications_router
from app.api.recipes import router as recipe_router
from app.api.timeline import router as timeline_router
from app.core.config import settings
from app.core.database import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(recipe_router, prefix=settings.api_prefix)
    app.include_router(batch_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)
    app.include_router(inventory_router, prefix=settings.api_prefix)
    app.include_router(timeline_router, prefix=settings.api_prefix)
    app.include_router(notifications_router, prefix=settings.api_prefix)
    return app


app = create_app()
