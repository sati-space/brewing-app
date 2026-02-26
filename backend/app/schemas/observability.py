from datetime import datetime

from pydantic import BaseModel


class RouteMetricsRead(BaseModel):
    method: str
    path: str
    count: int
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    client_errors: int
    server_errors: int


class ObservabilityMetricsResponse(BaseModel):
    generated_at: datetime
    uptime_seconds: int
    total_requests: int
    total_client_errors: int
    total_server_errors: int
    routes: list[RouteMetricsRead]
