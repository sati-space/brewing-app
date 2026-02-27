from pydantic import BaseModel, Field


class IonRangeRead(BaseModel):
    min_ppm: float = Field(ge=0)
    max_ppm: float = Field(ge=0)
    target_ppm: float = Field(ge=0)


class BJCPStyleRead(BaseModel):
    code: str
    name: str
    category: str
    impression: str
    examples: list[str] = Field(default_factory=list)
    calcium_ppm: IonRangeRead
    magnesium_ppm: IonRangeRead
    sodium_ppm: IonRangeRead
    chloride_ppm: IonRangeRead
    sulfate_ppm: IonRangeRead
    bicarbonate_ppm: IonRangeRead


class BJCPStyleListResponse(BaseModel):
    count: int
    items: list[BJCPStyleRead] = Field(default_factory=list)
