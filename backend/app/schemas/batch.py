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
    recorded_at: datetime | None = None


class FermentationReadingRead(FermentationReadingBase):
    id: int
    batch_id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FermentationTrendPointRead(BaseModel):
    id: int
    recorded_at: datetime
    gravity: float | None
    temp_c: float | None
    ph: float | None


class FermentationTrendRead(BaseModel):
    batch_id: int
    reading_count: int
    first_recorded_at: datetime | None
    latest_recorded_at: datetime | None
    latest_gravity: float | None
    latest_temp_c: float | None
    latest_ph: float | None
    gravity_drop: float | None
    average_hourly_gravity_drop: float | None
    plateau_risk: bool
    temperature_warning: bool
    alerts: list[str] = Field(default_factory=list)
    readings: list[FermentationTrendPointRead] = Field(default_factory=list)


class RecipeIngredientSnapshotRead(BaseModel):
    name: str
    ingredient_type: str
    amount: float
    unit: str
    stage: str
    minute_added: int


class BatchRecipeSnapshotRead(BaseModel):
    batch_id: int
    recipe_id: int
    captured_at: datetime | None
    name: str | None
    style: str | None
    target_og: float | None
    target_fg: float | None
    target_ibu: float | None
    target_srm: float | None
    efficiency_pct: float | None
    notes: str | None
    ingredients: list[RecipeIngredientSnapshotRead] = Field(default_factory=list)


class BatchInventoryRequirementRead(BaseModel):
    name: str
    ingredient_type: str
    required_amount: float
    required_unit: str
    available_amount: float
    shortage_amount: float
    enough_stock: bool
    inventory_item_id: int | None
    inventory_unit: str | None


class BatchInventoryPreviewRead(BaseModel):
    batch_id: int
    can_consume: bool
    shortage_count: int
    requirements: list[BatchInventoryRequirementRead] = Field(default_factory=list)


class BatchInventoryConsumeItemRead(BaseModel):
    inventory_item_id: int
    name: str
    consumed_amount: float
    consumed_unit: str
    quantity_before: float
    quantity_after: float


class BatchInventoryConsumeRead(BaseModel):
    batch_id: int
    consumed: bool
    consumed_at: datetime | None
    shortage_count: int
    items: list[BatchInventoryConsumeItemRead] = Field(default_factory=list)
    shortages: list[BatchInventoryRequirementRead] = Field(default_factory=list)
    detail: str
