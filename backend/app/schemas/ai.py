from pydantic import BaseModel, Field


class AISuggestion(BaseModel):
    title: str
    rationale: str
    action: str
    priority: str = Field(default="medium")


class RecipeOptimizeRequest(BaseModel):
    recipe_id: int = Field(gt=0)
    measured_og: float | None = Field(default=None, gt=1.0, lt=1.2)
    measured_fg: float | None = Field(default=None, gt=0.99, lt=1.2)


class RecipeOptimizeResponse(BaseModel):
    summary: str
    suggestions: list[AISuggestion]
    source: str = Field(default="rules")


class FermentationDiagnoseRequest(BaseModel):
    batch_id: int = Field(gt=0)


class FermentationDiagnoseResponse(BaseModel):
    summary: str
    suggestions: list[AISuggestion]
    source: str = Field(default="rules")
