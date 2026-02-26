from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.batch import Batch
from app.models.brew_step import BrewStep
from app.models.user import User
from app.schemas.timeline import UpcomingStepRead, UpcomingStepResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/upcoming-steps", response_model=UpcomingStepResponse)
def list_upcoming_steps(
    window_minutes: int = Query(default=120, ge=1, le=1440),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UpcomingStepResponse:
    now = datetime.utcnow()
    until = now + timedelta(minutes=window_minutes)

    rows = (
        db.query(BrewStep, Batch.name)
        .join(Batch, Batch.id == BrewStep.batch_id)
        .filter(
            BrewStep.owner_user_id == current_user.id,
            BrewStep.scheduled_for.isnot(None),
            BrewStep.status.in_(["pending", "in_progress"]),
            BrewStep.scheduled_for >= now,
            BrewStep.scheduled_for <= until,
        )
        .order_by(BrewStep.scheduled_for.asc(), BrewStep.step_order.asc())
        .all()
    )

    upcoming_steps: list[UpcomingStepRead] = []
    for step, batch_name in rows:
        scheduled_for = step.scheduled_for
        if scheduled_for is None:
            continue

        if scheduled_for.tzinfo is not None:
            scheduled_for_naive_utc = scheduled_for.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            scheduled_for_naive_utc = scheduled_for

        minutes_until = max(0, int((scheduled_for_naive_utc - now).total_seconds() // 60))

        upcoming_steps.append(
            UpcomingStepRead(
                id=step.id,
                batch_id=step.batch_id,
                batch_name=batch_name,
                step_order=step.step_order,
                name=step.name,
                scheduled_for=scheduled_for,
                minutes_until=minutes_until,
                status=step.status,
            )
        )

    return UpcomingStepResponse(
        window_minutes=window_minutes,
        count=len(upcoming_steps),
        steps=upcoming_steps,
    )
