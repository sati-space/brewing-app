from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.batch import Batch, FermentationReading
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.ai import (
    FermentationDiagnoseRequest,
    FermentationDiagnoseResponse,
    RecipeOptimizeRequest,
    RecipeOptimizeResponse,
)
from app.services import ai_orchestrator

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/recipe-optimize", response_model=RecipeOptimizeResponse)
def optimize_recipe(
    payload: RecipeOptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecipeOptimizeResponse:
    recipe = (
        db.query(Recipe)
        .filter(
            Recipe.id == payload.recipe_id,
            Recipe.owner_user_id == current_user.id,
        )
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    suggestions, source = ai_orchestrator.optimize_recipe(
        recipe=recipe,
        measured_og=payload.measured_og,
        measured_fg=payload.measured_fg,
    )

    return RecipeOptimizeResponse(
        summary=f"Generated {len(suggestions)} recommendation(s) for recipe '{recipe.name}'. Source: {source}.",
        suggestions=suggestions,
        source=source,
    )


@router.post("/fermentation-diagnose", response_model=FermentationDiagnoseResponse)
def diagnose_fermentation(
    payload: FermentationDiagnoseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FermentationDiagnoseResponse:
    batch = (
        db.query(Batch)
        .filter(
            Batch.id == payload.batch_id,
            Batch.owner_user_id == current_user.id,
        )
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    readings = db.query(FermentationReading).filter(FermentationReading.batch_id == batch.id).all()
    suggestions, source = ai_orchestrator.diagnose_fermentation(batch=batch, readings=readings)

    return FermentationDiagnoseResponse(
        summary=f"Generated {len(suggestions)} fermentation insight(s) for batch '{batch.name}'. Source: {source}.",
        suggestions=suggestions,
        source=source,
    )
