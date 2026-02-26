from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BrewStepBase(BaseModel):
    step_order: int = Field(default=1, ge=1, le=500)
    name: str = Field(min_length=1, max_length=140)
    description: str = ""
    scheduled_for: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=480)
    target_temp_c: float | None = Field(default=None, gt=-10, lt=120)
    status: str = Field(default="pending", max_length=20)


class BrewStepCreate(BrewStepBase):
    pass


class BrewStepUpdate(BaseModel):
    step_order: int | None = Field(default=None, ge=1, le=500)
    name: str | None = Field(default=None, min_length=1, max_length=140)
    description: str | None = None
    scheduled_for: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=480)
    target_temp_c: float | None = Field(default=None, gt=-10, lt=120)
    status: str | None = Field(default=None, max_length=20)


class BrewStepRead(BrewStepBase):
    id: int
    batch_id: int
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpcomingStepRead(BaseModel):
    id: int
    batch_id: int
    batch_name: str
    step_order: int
    name: str
    scheduled_for: datetime
    minutes_until: int
    status: str


class UpcomingStepResponse(BaseModel):
    window_minutes: int
    count: int
    steps: list[UpcomingStepRead]
