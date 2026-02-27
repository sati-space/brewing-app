from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ingredients import IngredientProfileRead


class ExternalImportRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=60)
    external_id: str = Field(min_length=1, max_length=120)


class ExternalRecipeCatalogIngredientRead(BaseModel):
    name: str
    ingredient_type: str
    amount: float
    unit: str
    stage: str
    minute_added: int


class ExternalRecipeCatalogItemRead(BaseModel):
    provider: str
    external_id: str
    name: str
    style: str
    target_og: float
    target_fg: float
    target_ibu: float
    target_srm: float
    efficiency_pct: float
    notes: str
    ingredients: list[ExternalRecipeCatalogIngredientRead] = Field(default_factory=list)


class ExternalRecipeCatalogResponse(BaseModel):
    count: int
    items: list[ExternalRecipeCatalogItemRead] = Field(default_factory=list)


class RecipeImportResultRead(BaseModel):
    provider: str
    external_id: str
    recipe_id: int
    recipe_name: str


class ExternalEquipmentCatalogItemRead(BaseModel):
    provider: str
    external_id: str
    name: str
    batch_volume_liters: float
    mash_tun_volume_liters: float | None
    boil_kettle_volume_liters: float | None
    brewhouse_efficiency_pct: float
    boil_off_rate_l_per_hour: float | None
    trub_loss_liters: float | None
    notes: str


class ExternalEquipmentCatalogResponse(BaseModel):
    count: int
    items: list[ExternalEquipmentCatalogItemRead] = Field(default_factory=list)


class EquipmentProfileRead(BaseModel):
    id: int
    source_provider: str
    source_external_id: str
    name: str
    batch_volume_liters: float
    mash_tun_volume_liters: float | None
    boil_kettle_volume_liters: float | None
    brewhouse_efficiency_pct: float
    boil_off_rate_l_per_hour: float | None
    trub_loss_liters: float | None
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EquipmentImportResultRead(BaseModel):
    provider: str
    external_id: str
    equipment_profile: EquipmentProfileRead


class ExternalIngredientCatalogItemRead(BaseModel):
    provider: str
    external_id: str
    name: str
    ingredient_type: str
    default_unit: str
    notes: str


class ExternalIngredientCatalogResponse(BaseModel):
    count: int
    items: list[ExternalIngredientCatalogItemRead] = Field(default_factory=list)


class IngredientImportResultRead(BaseModel):
    provider: str
    external_id: str
    ingredient_profile: IngredientProfileRead
