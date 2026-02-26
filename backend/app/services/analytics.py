from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.recipe import Recipe
from app.schemas.analytics import AnalyticsOverviewRead, RecentBatchInsight, StyleBatchCount
from app.services.recipe_calculator import attenuation_pct, estimate_abv


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def build_overview(db: Session, user_id: int) -> AnalyticsOverviewRead:
    total_recipes = db.query(func.count(Recipe.id)).filter(Recipe.owner_user_id == user_id).scalar() or 0

    total_batches = db.query(func.count(Batch.id)).filter(Batch.owner_user_id == user_id).scalar() or 0

    completed_batches = (
        db.query(func.count(Batch.id))
        .filter(
            Batch.owner_user_id == user_id,
            Batch.status.in_(("completed", "packaged")),
        )
        .scalar()
        or 0
    )

    gravity_rows = (
        db.query(Batch.measured_og, Batch.measured_fg)
        .filter(
            Batch.owner_user_id == user_id,
            Batch.measured_og.isnot(None),
            Batch.measured_fg.isnot(None),
        )
        .all()
    )

    abv_values: list[float] = []
    attenuation_values: list[float] = []
    for measured_og, measured_fg in gravity_rows:
        if measured_og is None or measured_fg is None:
            continue
        if measured_og <= measured_fg or measured_og <= 1.0:
            continue

        abv_values.append(estimate_abv(measured_og, measured_fg))
        attenuation_values.append(attenuation_pct(measured_og, measured_fg))

    style_rows = (
        db.query(
            Recipe.style,
            func.count(Batch.id).label("batch_count"),
        )
        .join(Batch, Batch.recipe_id == Recipe.id)
        .filter(Batch.owner_user_id == user_id)
        .group_by(Recipe.style)
        .order_by(desc("batch_count"), Recipe.style.asc())
        .all()
    )
    style_breakdown = [
        StyleBatchCount(style=style or "Unknown", batch_count=batch_count)
        for style, batch_count in style_rows
    ]

    recent_batch_rows = (
        db.query(Batch)
        .filter(Batch.owner_user_id == user_id)
        .order_by(Batch.brewed_on.desc(), Batch.id.desc())
        .limit(5)
        .all()
    )
    recent_batches = [
        RecentBatchInsight(
            id=batch.id,
            name=batch.name,
            status=batch.status,
            brewed_on=batch.brewed_on,
            abv=(
                estimate_abv(batch.measured_og, batch.measured_fg)
                if batch.measured_og is not None and batch.measured_fg is not None and batch.measured_og > batch.measured_fg
                else None
            ),
        )
        for batch in recent_batch_rows
    ]

    return AnalyticsOverviewRead(
        total_recipes=total_recipes,
        total_batches=total_batches,
        completed_batches=completed_batches,
        average_abv=_avg(abv_values),
        average_attenuation_pct=_avg(attenuation_values),
        style_breakdown=style_breakdown,
        recent_batches=recent_batches,
    )
