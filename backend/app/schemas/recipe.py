from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecipeIngredientBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    ingredient_type: str = Field(min_length=1, max_length=30)
    amount: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)
    stage: str = Field(default="boil", max_length=30)
    minute_added: int = Field(default=0, ge=0)


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredientRead(RecipeIngredientBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RecipeBase(BaseModel):
    name: str = Field(min_length=1, max_length=140)
    style: str = Field(default="Unknown", max_length=80)
    target_og: float = Field(gt=1.0, lt=1.2)
    target_fg: float = Field(gt=0.99, lt=1.2)
    target_ibu: float = Field(ge=0, le=150)
    target_srm: float = Field(ge=0, le=80)
    efficiency_pct: float = Field(default=70, ge=30, le=95)
    notes: str = ""


class RecipeCreate(RecipeBase):
    ingredients: list[RecipeIngredientCreate] = Field(default_factory=list)


class RecipeRead(RecipeBase):
    id: int
    created_at: datetime
    ingredients: list[RecipeIngredientRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
