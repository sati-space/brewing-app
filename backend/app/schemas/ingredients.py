from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IngredientProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    ingredient_type: str = Field(min_length=1, max_length=30)
    default_unit: str = Field(min_length=1, max_length=20)
    notes: str = ""


class IngredientProfileCreate(IngredientProfileBase):
    pass


class IngredientProfileUpdate(IngredientProfileBase):
    pass


class IngredientProfileRead(IngredientProfileBase):
    id: int
    source_provider: str | None
    source_external_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
