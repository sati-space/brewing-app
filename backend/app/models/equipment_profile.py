from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class EquipmentProfile(Base):
    __tablename__ = "equipment_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    source_provider: Mapped[str] = mapped_column(String(60), nullable=False)
    source_external_id: Mapped[str] = mapped_column(String(120), nullable=False)

    name: Mapped[str] = mapped_column(String(140), nullable=False)
    batch_volume_liters: Mapped[float] = mapped_column(Float, nullable=False)
    mash_tun_volume_liters: Mapped[float | None] = mapped_column(Float, nullable=True)
    boil_kettle_volume_liters: Mapped[float | None] = mapped_column(Float, nullable=True)
    brewhouse_efficiency_pct: Mapped[float] = mapped_column(Float, nullable=False)
    boil_off_rate_l_per_hour: Mapped[float | None] = mapped_column(Float, nullable=True)
    trub_loss_liters: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner: Mapped[User] = relationship(back_populates="equipment_profiles")
