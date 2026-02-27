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


class RecipeScaleRequest(BaseModel):
    source_batch_volume_liters: float = Field(default=20.0, gt=0)
    target_batch_volume_liters: float = Field(gt=0)
    equipment_profile_id: int | None = Field(default=None, gt=0)
    target_efficiency_pct: float | None = Field(default=None, gt=0, le=100)


class ScaledRecipeIngredientRead(BaseModel):
    name: str
    ingredient_type: str
    original_amount: float
    scaled_amount: float
    unit: str
    stage: str
    minute_added: int


class RecipeScaleRead(BaseModel):
    recipe_id: int
    recipe_name: str
    style: str
    source_batch_volume_liters: float
    target_batch_volume_liters: float
    scale_factor: float
    source_efficiency_pct: float
    target_efficiency_pct: float
    estimated_target_og: float
    estimated_target_fg: float
    estimated_abv: float
    target_ibu: float
    target_srm: float
    ingredients: list[ScaledRecipeIngredientRead] = Field(default_factory=list)


class RecipeHopSubstitutionRequest(BaseModel):
    target_hop_name: str = Field(min_length=1, max_length=120)
    available_hop_names: list[str] = Field(default_factory=list, max_length=50)
    include_inventory_hops: bool = True
    top_k: int = Field(default=5, ge=1, le=10)


class HopProfileRead(BaseModel):
    name: str
    alpha_acid_min_pct: float
    alpha_acid_max_pct: float
    flavor_descriptors: list[str] = Field(default_factory=list)


class HopSubstitutionCandidateRead(BaseModel):
    name: str
    alpha_acid_min_pct: float
    alpha_acid_max_pct: float
    flavor_similarity_score: float
    descriptor_overlap_score: float
    similarity_score: float
    recommended_bittering_ratio: float
    shared_descriptors: list[str] = Field(default_factory=list)


class RecipeHopSubstitutionRead(BaseModel):
    recipe_id: int
    recipe_name: str
    target_hop_name: str
    target_hop_profile: HopProfileRead
    candidate_source: str
    candidate_input_count: int
    recognized_candidate_count: int
    unresolved_hop_names: list[str] = Field(default_factory=list)
    substitutions: list[HopSubstitutionCandidateRead] = Field(default_factory=list)
