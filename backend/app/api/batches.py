from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.batch import Batch, FermentationReading
from app.models.recipe import Recipe
from app.schemas.batch import (
    BatchCreate,
    BatchRead,
    FermentationReadingCreate,
    FermentationReadingRead,
)

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=BatchRead, status_code=201)
def create_batch(payload: BatchCreate, db: Session = Depends(get_db)) -> Batch:
    recipe_exists = db.query(Recipe.id).filter(Recipe.id == payload.recipe_id).first()
    if not recipe_exists:
        raise HTTPException(status_code=404, detail="Recipe not found")

    batch = Batch(
        recipe_id=payload.recipe_id,
        name=payload.name,
        brewed_on=payload.brewed_on,
        status=payload.status,
        volume_liters=payload.volume_liters,
        measured_og=payload.measured_og,
        measured_fg=payload.measured_fg,
        notes=payload.notes,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("", response_model=list[BatchRead])
def list_batches(db: Session = Depends(get_db)) -> list[Batch]:
    return db.query(Batch).order_by(Batch.created_at.desc()).all()


@router.post("/{batch_id}/readings", response_model=FermentationReadingRead, status_code=201)
def add_fermentation_reading(
    batch_id: int,
    payload: FermentationReadingCreate,
    db: Session = Depends(get_db),
) -> FermentationReading:
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    reading = FermentationReading(
        batch_id=batch.id,
        gravity=payload.gravity,
        temp_c=payload.temp_c,
        ph=payload.ph,
        notes=payload.notes,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading
