from sqlalchemy.orm import Session

from app.models.batch import Batch, FermentationReading
from app.schemas.batch import FermentationTrendPointRead, FermentationTrendRead


def build_fermentation_trend(db: Session, batch_id: int, user_id: int) -> FermentationTrendRead | None:
    batch = (
        db.query(Batch)
        .filter(
            Batch.id == batch_id,
            Batch.owner_user_id == user_id,
        )
        .first()
    )
    if not batch:
        return None

    readings = (
        db.query(FermentationReading)
        .filter(FermentationReading.batch_id == batch_id)
        .order_by(FermentationReading.recorded_at.asc(), FermentationReading.id.asc())
        .all()
    )

    points = [
        FermentationTrendPointRead(
            id=reading.id,
            recorded_at=reading.recorded_at,
            gravity=reading.gravity,
            temp_c=reading.temp_c,
            ph=reading.ph,
        )
        for reading in readings
    ]

    first_recorded_at = readings[0].recorded_at if readings else None
    latest = readings[-1] if readings else None

    gravity_observations = [
        (reading.recorded_at, reading.gravity)
        for reading in readings
        if reading.gravity is not None
    ]

    gravity_drop: float | None = None
    average_hourly_gravity_drop: float | None = None
    if len(gravity_observations) >= 2:
        first_time, first_gravity = gravity_observations[0]
        last_time, last_gravity = gravity_observations[-1]

        raw_drop = first_gravity - last_gravity
        gravity_drop = round(raw_drop, 4)

        elapsed_hours = (last_time - first_time).total_seconds() / 3600
        if elapsed_hours > 0:
            average_hourly_gravity_drop = round(raw_drop / elapsed_hours, 5)

    plateau_risk = False
    if len(gravity_observations) >= 3:
        _, g1 = gravity_observations[-3]
        _, g2 = gravity_observations[-2]
        _, g3 = gravity_observations[-1]
        gravity_window = max(g1, g2, g3) - min(g1, g2, g3)
        plateau_risk = gravity_window <= 0.0015 and g3 > 1.020

    latest_temp = latest.temp_c if latest else None
    temperature_warning = latest_temp is not None and (latest_temp < 16.0 or latest_temp > 24.0)

    alerts: list[str] = []
    if not readings:
        alerts.append("No fermentation readings logged yet.")
    else:
        if plateau_risk:
            alerts.append("Gravity has flattened recently while still high. Check yeast health and fermentation conditions.")

        if latest_temp is not None and latest_temp > 24.0:
            alerts.append("Latest fermentation temperature is high for many ale profiles.")
        elif latest_temp is not None and latest_temp < 16.0:
            alerts.append("Latest fermentation temperature is low and may slow yeast activity.")

        if not alerts:
            alerts.append("Fermentation trend appears stable.")

    return FermentationTrendRead(
        batch_id=batch_id,
        reading_count=len(readings),
        first_recorded_at=first_recorded_at,
        latest_recorded_at=latest.recorded_at if latest else None,
        latest_gravity=latest.gravity if latest else None,
        latest_temp_c=latest.temp_c if latest else None,
        latest_ph=latest.ph if latest else None,
        gravity_drop=gravity_drop,
        average_hourly_gravity_drop=average_hourly_gravity_drop,
        plateau_risk=plateau_risk,
        temperature_warning=temperature_warning,
        alerts=alerts,
        readings=points,
    )
