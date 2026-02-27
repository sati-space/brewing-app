from datetime import date, datetime
from typing import Literal

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


class BrewPlanRequest(BaseModel):
    equipment_profile_id: int | None = Field(default=None, gt=0)
    water_profile_id: int | None = Field(default=None, gt=0)
    style_code: str | None = Field(default=None, min_length=1, max_length=20)
    available_hop_names: list[str] = Field(default_factory=list, max_length=50)
    brew_start_at: datetime | None = None
    unit_system: Literal["metric", "imperial"] | None = None
    temperature_unit: Literal["C", "F"] | None = None
    language: Literal["en", "es"] | None = None


class BrewPlanVolumeRead(BaseModel):
    grain_bill_kg: float
    mash_water_liters: float
    sparge_water_liters: float
    total_water_liters: float
    pre_boil_volume_liters: float
    post_boil_volume_liters: float
    estimated_boil_off_liters: float
    mash_target_temp_c: float
    strike_water_temp_c: float
    mash_rest_minutes: int
    sparge_minutes: int
    boil_minutes: int


class BrewPlanGravityRead(BaseModel):
    source_target_og: float
    source_target_fg: float
    estimated_og: float
    estimated_fg: float
    estimated_abv: float
    fermentable_inventory_coverage_pct: float
    source_efficiency_pct: float
    target_efficiency_pct: float


class BrewPlanEquipmentRead(BaseModel):
    equipment_profile_id: int | None
    equipment_name: str | None
    batch_volume_liters: float | None
    mash_tun_volume_liters: float | None
    boil_kettle_volume_liters: float | None
    boil_off_rate_l_per_hour: float
    trub_loss_liters: float


class BrewPlanHopCandidateRead(BaseModel):
    name: str
    similarity_score: float
    recommended_bittering_ratio: float
    shared_descriptors: list[str] = Field(default_factory=list)


class BrewPlanHopSubstitutionRead(BaseModel):
    target_hop_name: str
    missing_amount: float
    unit: str
    candidates: list[BrewPlanHopCandidateRead] = Field(default_factory=list)


class BrewPlanShoppingItemRead(BaseModel):
    name: str
    ingredient_type: str
    required_amount: float
    required_unit: str
    available_amount: float
    shortage_amount: float
    suggested_substitutions: list[str] = Field(default_factory=list)


class BrewPlanStepRead(BaseModel):
    step_order: int
    timer_key: str
    name: str
    duration_minutes: int
    target_temp_c: float | None
    start_offset_minutes: int
    planned_start_at: datetime | None
    planned_end_at: datetime | None


class BrewPlanWaterIonRead(BaseModel):
    calcium_ppm: float
    magnesium_ppm: float
    sodium_ppm: float
    chloride_ppm: float
    sulfate_ppm: float
    bicarbonate_ppm: float


class BrewPlanMineralAdditionRead(BaseModel):
    mineral_name: str
    grams_per_liter: float
    grams_total: float
    reason: str


class BrewPlanWaterRead(BaseModel):
    water_profile_id: int
    water_profile_name: str
    style_code: str
    style_name: str
    source_profile: BrewPlanWaterIonRead
    target_profile: BrewPlanWaterIonRead
    projected_profile: BrewPlanWaterIonRead
    additions: list[BrewPlanMineralAdditionRead] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BrewPlanRead(BaseModel):
    batch_id: int
    batch_name: str
    style: str
    generated_at: datetime
    unit_system: Literal["metric", "imperial"]
    temperature_unit: Literal["C", "F"]
    language: Literal["en", "es"]
    volumes: BrewPlanVolumeRead
    gravity: BrewPlanGravityRead
    equipment: BrewPlanEquipmentRead
    inventory_shortage_count: int
    shopping_list: list[BrewPlanShoppingItemRead] = Field(default_factory=list)
    hop_substitutions: list[BrewPlanHopSubstitutionRead] = Field(default_factory=list)
    water_recommendation: BrewPlanWaterRead | None
    timer_plan: list[BrewPlanStepRead] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BrewPlanDisplayUnitsRead(BaseModel):
    unit_system: Literal["metric", "imperial"]
    language: Literal["en", "es"]
    grain_unit: str
    volume_unit: str
    temperature_unit: Literal["C", "F"]


class BrewPlanDisplayRead(BaseModel):
    grain_bill: float
    mash_water: float
    sparge_water: float
    total_water: float
    pre_boil_volume: float
    post_boil_volume: float
    boil_off: float
    mash_target_temp: float
    strike_water_temp: float


class BrewPlanLocalizedRead(BrewPlanRead):
    display_units: BrewPlanDisplayUnitsRead
    display: BrewPlanDisplayRead


class BrewPlanApplyTimelineRequest(BrewPlanRequest):
    replace_existing_pending_steps: bool = True
    include_shopping_step: bool = True
    include_water_step: bool = True


class BrewPlanAppliedStepRead(BaseModel):
    step_id: int
    step_order: int
    timer_key: str
    name: str
    status: str
    scheduled_for: datetime | None
    duration_minutes: int | None
    target_temp_c: float | None


class BrewPlanApplyTimelineRead(BaseModel):
    batch_id: int
    generated_at: datetime
    deleted_step_count: int
    preserved_step_count: int
    created_step_count: int
    steps: list[BrewPlanAppliedStepRead] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
