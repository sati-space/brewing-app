from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.batch import Batch
from app.models.brew_step import BrewStep
from app.models.user import User
from app.schemas.timeline import BrewStepCreate, BrewStepRead, BrewStepUpdate

router = APIRouter(prefix="/batches/{batch_id}/timeline", tags=["timeline"])

VALID_STATUSES = {"pending", "in_progress", "completed", "skipped"}


def _ensure_batch_owned(db: Session, batch_id: int, user_id: int) -> Batch:
    batch = (
        db.query(Batch)
        .filter(
            Batch.id == batch_id,
            Batch.owner_user_id == user_id,
        )
        .first()
    )
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return batch


@router.post("/steps", response_model=BrewStepRead, status_code=status.HTTP_201_CREATED)
def create_brew_step(
    batch_id: int,
    payload: BrewStepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrewStep:
    _ensure_batch_owned(db=db, batch_id=batch_id, user_id=current_user.id)

    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid step status")

    completed_at = datetime.utcnow() if payload.status == "completed" else None

    step = BrewStep(
        batch_id=batch_id,
        owner_user_id=current_user.id,
        step_order=payload.step_order,
        name=payload.name,
        description=payload.description,
        scheduled_for=payload.scheduled_for,
        duration_minutes=payload.duration_minutes,
        target_temp_c=payload.target_temp_c,
        status=payload.status,
        completed_at=completed_at,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


@router.get("/steps", response_model=list[BrewStepRead])
def list_brew_steps(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BrewStep]:
    _ensure_batch_owned(db=db, batch_id=batch_id, user_id=current_user.id)

    return (
        db.query(BrewStep)
        .filter(
            BrewStep.batch_id == batch_id,
            BrewStep.owner_user_id == current_user.id,
        )
        .order_by(BrewStep.step_order.asc(), BrewStep.created_at.asc())
        .all()
    )


@router.patch("/steps/{step_id}", response_model=BrewStepRead)
def update_brew_step(
    batch_id: int,
    step_id: int,
    payload: BrewStepUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrewStep:
    _ensure_batch_owned(db=db, batch_id=batch_id, user_id=current_user.id)

    step = (
        db.query(BrewStep)
        .filter(
            BrewStep.id == step_id,
            BrewStep.batch_id == batch_id,
            BrewStep.owner_user_id == current_user.id,
        )
        .first()
    )
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timeline step not found")

    updates = payload.model_dump(exclude_unset=True)
    new_status = updates.get("status")
    if new_status is not None and new_status not in VALID_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid step status")

    for field, value in updates.items():
        setattr(step, field, value)

    if new_status == "completed":
        step.completed_at = datetime.utcnow()
    elif new_status is not None:
        step.completed_at = None

    db.add(step)
    db.commit()
    db.refresh(step)
    return step
