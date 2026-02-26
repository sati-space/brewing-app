from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock


@dataclass
class RouteStats:
    method: str
    path: str
    count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    client_errors: int = 0
    server_errors: int = 0

    def record(self, duration_ms: float, status_code: int) -> None:
        self.count += 1
        self.total_latency_ms += duration_ms

        if self.count == 1:
            self.min_latency_ms = duration_ms
            self.max_latency_ms = duration_ms
        else:
            self.min_latency_ms = min(self.min_latency_ms, duration_ms)
            self.max_latency_ms = max(self.max_latency_ms, duration_ms)

        if 400 <= status_code <= 499:
            self.client_errors += 1
        elif status_code >= 500:
            self.server_errors += 1

    @property
    def avg_latency_ms(self) -> float:
        if self.count == 0:
            return 0.0
        return self.total_latency_ms / self.count


class ObservabilityTracker:
    def __init__(self) -> None:
        self._lock = Lock()
        self._started_at = datetime.utcnow()
        self._total_requests = 0
        self._total_client_errors = 0
        self._total_server_errors = 0
        self._routes: dict[tuple[str, str], RouteStats] = {}

    def reset(self) -> None:
        with self._lock:
            self._started_at = datetime.utcnow()
            self._total_requests = 0
            self._total_client_errors = 0
            self._total_server_errors = 0
            self._routes = {}

    def record(self, *, method: str, path: str, status_code: int, duration_ms: float) -> None:
        key = (method, path)
        with self._lock:
            route = self._routes.get(key)
            if route is None:
                route = RouteStats(method=method, path=path)
                self._routes[key] = route

            route.record(duration_ms=duration_ms, status_code=status_code)

            self._total_requests += 1
            if 400 <= status_code <= 499:
                self._total_client_errors += 1
            elif status_code >= 500:
                self._total_server_errors += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            now = datetime.utcnow()
            uptime_seconds = int((now - self._started_at).total_seconds())

            routes = [
                {
                    "method": route.method,
                    "path": route.path,
                    "count": route.count,
                    "avg_latency_ms": round(route.avg_latency_ms, 2),
                    "min_latency_ms": round(route.min_latency_ms, 2),
                    "max_latency_ms": round(route.max_latency_ms, 2),
                    "client_errors": route.client_errors,
                    "server_errors": route.server_errors,
                }
                for route in sorted(self._routes.values(), key=lambda item: (item.path, item.method))
            ]

            return {
                "generated_at": now,
                "uptime_seconds": uptime_seconds,
                "total_requests": self._total_requests,
                "total_client_errors": self._total_client_errors,
                "total_server_errors": self._total_server_errors,
                "routes": routes,
            }


observability_tracker = ObservabilityTracker()
