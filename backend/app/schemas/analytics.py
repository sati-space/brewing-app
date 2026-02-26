from datetime import date

from pydantic import BaseModel


class StyleBatchCount(BaseModel):
    style: str
    batch_count: int


class RecentBatchInsight(BaseModel):
    id: int
    name: str
    status: str
    brewed_on: date
    abv: float | None


class AnalyticsOverviewRead(BaseModel):
    total_recipes: int
    total_batches: int
    completed_batches: int
    average_abv: float | None
    average_attenuation_pct: float | None
    style_breakdown: list[StyleBatchCount]
    recent_batches: list[RecentBatchInsight]
