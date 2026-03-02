from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api.ai import router as ai_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.batches import router as batch_router
from app.api.equipment import router as equipment_router
from app.api.health import router as health_router
from app.api.imports import router as imports_router
from app.api.ingredients import router as ingredients_router
from app.api.inventory import router as inventory_router
from app.api.notifications import router as notifications_router
from app.api.observability import router as observability_router
from app.api.recipes import router as recipe_router
from app.api.styles import router as styles_router
from app.api.timeline import router as timeline_router
from app.api.water_profiles import router as water_profiles_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.observability_middleware import ObservabilityMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(ObservabilityMiddleware)
    origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(recipe_router, prefix=settings.api_prefix)
    app.include_router(styles_router, prefix=settings.api_prefix)
    app.include_router(batch_router, prefix=settings.api_prefix)
    app.include_router(analytics_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)
    app.include_router(imports_router, prefix=settings.api_prefix)
    app.include_router(ingredients_router, prefix=settings.api_prefix)
    app.include_router(equipment_router, prefix=settings.api_prefix)
    app.include_router(inventory_router, prefix=settings.api_prefix)
    app.include_router(timeline_router, prefix=settings.api_prefix)
    app.include_router(notifications_router, prefix=settings.api_prefix)
    app.include_router(observability_router, prefix=settings.api_prefix)
    app.include_router(water_profiles_router, prefix=settings.api_prefix)
    return app


app = create_app()
