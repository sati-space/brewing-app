from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    style: Mapped[str] = mapped_column(String(80), default="Unknown")
    target_og: Mapped[float] = mapped_column(Float, nullable=False)
    target_fg: Mapped[float] = mapped_column(Float, nullable=False)
    target_ibu: Mapped[float] = mapped_column(Float, nullable=False)
    target_srm: Mapped[float] = mapped_column(Float, nullable=False)
    efficiency_pct: Mapped[float] = mapped_column(Float, default=70.0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    ingredient_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    stage: Mapped[str] = mapped_column(String(30), default="boil")
    minute_added: Mapped[int] = mapped_column(default=0)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
