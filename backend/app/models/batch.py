from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.brew_step import BrewStep
    from app.models.user import User


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    brewed_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="planned")
    volume_liters: Mapped[float] = mapped_column(Float, nullable=False)
    measured_og: Mapped[float | None] = mapped_column(Float, nullable=True)
    measured_fg: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    recipe_snapshot_captured_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    recipe_name_snapshot: Mapped[str | None] = mapped_column(String(140), nullable=True)
    recipe_style_snapshot: Mapped[str | None] = mapped_column(String(80), nullable=True)
    recipe_target_og_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    recipe_target_fg_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    recipe_target_ibu_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    recipe_target_srm_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    recipe_efficiency_pct_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    recipe_notes_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipe_ingredients_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped[User] = relationship(back_populates="batches")
    readings: Mapped[list[FermentationReading]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    brew_steps: Mapped[list[BrewStep]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )


class FermentationReading(Base):
    __tablename__ = "fermentation_readings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    gravity: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    batch: Mapped[Batch] = relationship(back_populates="readings")
