from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class WaterProfile(Base):
    __tablename__ = "water_profiles"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "name", name="uq_water_profile_owner_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    calcium_ppm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    magnesium_ppm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sodium_ppm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    chloride_ppm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sulfate_ppm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    bicarbonate_ppm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    owner: Mapped[User] = relationship(back_populates="water_profiles")
