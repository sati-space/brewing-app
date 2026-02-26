from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.observability import ObservabilityMetricsResponse
from app.services.observability import observability_tracker

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/metrics", response_model=ObservabilityMetricsResponse)
def get_metrics(current_user: User = Depends(get_current_user)) -> ObservabilityMetricsResponse:
    _ = current_user
    return ObservabilityMetricsResponse(**observability_tracker.snapshot())
