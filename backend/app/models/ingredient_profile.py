from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class IngredientProfile(Base):
    __tablename__ = "ingredient_profiles"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "name", "ingredient_type", name="uq_ingredient_profile_name_type"),
        UniqueConstraint("owner_user_id", "source_provider", "source_external_id", name="uq_ingredient_profile_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    source_provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    source_external_id: Mapped[str | None] = mapped_column(String(120), nullable=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    ingredient_type: Mapped[str] = mapped_column(String(30), nullable=False)
    default_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner: Mapped[User] = relationship(back_populates="ingredient_profiles")
