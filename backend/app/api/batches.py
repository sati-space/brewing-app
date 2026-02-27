from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.batch import Batch, FermentationReading
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.batch import (
    BatchCreate,
    BatchRead,
    BatchRecipeSnapshotRead,
    FermentationReadingCreate,
    FermentationReadingRead,
    FermentationTrendRead,
    RecipeIngredientSnapshotRead,
)
from app.services.batch_snapshot import apply_recipe_snapshot, parse_snapshot_ingredients
from app.services.fermentation import build_fermentation_trend

router = APIRouter(prefix="/batches", tags=["batches"])


def _get_user_batch_or_404(db: Session, batch_id: int, user_id: int) -> Batch:
    batch = (
        db.query(Batch)
        .filter(
            Batch.id == batch_id,
            Batch.owner_user_id == user_id,
        )
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.post("", response_model=BatchRead, status_code=201)
def create_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Batch:
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

    batch = Batch(
        owner_user_id=current_user.id,
        recipe_id=payload.recipe_id,
        name=payload.name,
        brewed_on=payload.brewed_on,
        status=payload.status,
        volume_liters=payload.volume_liters,
        measured_og=payload.measured_og,
        measured_fg=payload.measured_fg,
        notes=payload.notes,
    )
    apply_recipe_snapshot(batch, recipe)

    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("", response_model=list[BatchRead])
def list_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Batch]:
    return (
        db.query(Batch)
        .filter(Batch.owner_user_id == current_user.id)
        .order_by(Batch.created_at.desc())
        .all()
    )


@router.get("/{batch_id}/recipe-snapshot", response_model=BatchRecipeSnapshotRead)
def get_batch_recipe_snapshot(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchRecipeSnapshotRead:
    batch = _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)

    ingredient_payload = parse_snapshot_ingredients(batch)
    ingredients = [
        RecipeIngredientSnapshotRead(**item)
        for item in ingredient_payload
    ]

    return BatchRecipeSnapshotRead(
        batch_id=batch.id,
        recipe_id=batch.recipe_id,
        captured_at=batch.recipe_snapshot_captured_at or batch.created_at,
        name=batch.recipe_name_snapshot,
        style=batch.recipe_style_snapshot,
        target_og=batch.recipe_target_og_snapshot,
        target_fg=batch.recipe_target_fg_snapshot,
        target_ibu=batch.recipe_target_ibu_snapshot,
        target_srm=batch.recipe_target_srm_snapshot,
        efficiency_pct=batch.recipe_efficiency_pct_snapshot,
        notes=batch.recipe_notes_snapshot,
        ingredients=ingredients,
    )


@router.post("/{batch_id}/readings", response_model=FermentationReadingRead, status_code=201)
def add_fermentation_reading(
    batch_id: int,
    payload: FermentationReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FermentationReading:
    batch = _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)

    reading = FermentationReading(
        batch_id=batch.id,
        recorded_at=payload.recorded_at or datetime.utcnow(),
        gravity=payload.gravity,
        temp_c=payload.temp_c,
        ph=payload.ph,
        notes=payload.notes,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/{batch_id}/readings", response_model=list[FermentationReadingRead])
def list_fermentation_readings(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FermentationReading]:
    _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)

    return (
        db.query(FermentationReading)
        .filter(FermentationReading.batch_id == batch_id)
        .order_by(FermentationReading.recorded_at.asc(), FermentationReading.id.asc())
        .all()
    )


@router.get("/{batch_id}/fermentation/trend", response_model=FermentationTrendRead)
def get_fermentation_trend(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FermentationTrendRead:
    trend = build_fermentation_trend(db, batch_id=batch_id, user_id=current_user.id)
    if trend is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return trend
