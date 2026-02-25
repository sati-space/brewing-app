from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BatchBase(BaseModel):
    recipe_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=140)
    brewed_on: date
    status: str = Field(default="planned", max_length=30)
    volume_liters: float = Field(gt=0)
    measured_og: float | None = Field(default=None, gt=1.0, lt=1.2)
    measured_fg: float | None = Field(default=None, gt=0.99, lt=1.2)
    notes: str = ""


class BatchCreate(BatchBase):
    pass


class BatchRead(BatchBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FermentationReadingBase(BaseModel):
    gravity: float | None = Field(default=None, gt=0.99, lt=1.2)
    temp_c: float | None = Field(default=None, gt=-10, lt=60)
    ph: float | None = Field(default=None, gt=0, lt=14)
    notes: str = ""


class FermentationReadingCreate(FermentationReadingBase):
    pass


class FermentationReadingRead(FermentationReadingBase):
    id: int
    batch_id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
