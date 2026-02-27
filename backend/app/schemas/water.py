from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WaterProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    calcium_ppm: float = Field(default=0.0, ge=0, le=600)
    magnesium_ppm: float = Field(default=0.0, ge=0, le=200)
    sodium_ppm: float = Field(default=0.0, ge=0, le=400)
    chloride_ppm: float = Field(default=0.0, ge=0, le=800)
    sulfate_ppm: float = Field(default=0.0, ge=0, le=800)
    bicarbonate_ppm: float = Field(default=0.0, ge=0, le=600)
    notes: str = ""


class WaterProfileCreate(WaterProfileBase):
    pass


class WaterProfileUpdate(WaterProfileBase):
    pass


class WaterProfileRead(WaterProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WaterRecommendationRequest(BaseModel):
    style_code: str | None = Field(default=None, min_length=1, max_length=20)
    recipe_id: int | None = Field(default=None, gt=0)
    batch_volume_liters: float = Field(default=20.0, gt=0, le=300)


class MineralAdditionRead(BaseModel):
    mineral_name: str
    grams_per_liter: float
    grams_total: float
    reason: str


class WaterIonSnapshotRead(BaseModel):
    calcium_ppm: float
    magnesium_ppm: float
    sodium_ppm: float
    chloride_ppm: float
    sulfate_ppm: float
    bicarbonate_ppm: float


class WaterRecommendationRead(BaseModel):
    water_profile_id: int
    water_profile_name: str
    style_code: str
    style_name: str
    batch_volume_liters: float
    source_profile: WaterIonSnapshotRead
    target_profile: WaterIonSnapshotRead
    projected_profile: WaterIonSnapshotRead
    additions: list[MineralAdditionRead] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
