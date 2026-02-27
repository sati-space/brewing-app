from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.brew_step import BrewStep
    from app.models.equipment_profile import EquipmentProfile
    from app.models.inventory import InventoryItem
    from app.models.recipe import Recipe


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    recipes: Mapped[list[Recipe]] = relationship(back_populates="owner")
    batches: Mapped[list[Batch]] = relationship(back_populates="owner")
    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates="owner")
    brew_steps: Mapped[list[BrewStep]] = relationship(back_populates="owner")
    equipment_profiles: Mapped[list[EquipmentProfile]] = relationship(back_populates="owner")
