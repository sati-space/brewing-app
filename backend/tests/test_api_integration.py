from collections.abc import Generator
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.batches import router as batch_router
from app.api.health import router as health_router
from app.api.inventory import router as inventory_router
from app.api.notifications import router as notifications_router
from app.api.observability import router as observability_router
from app.api.recipes import router as recipe_router
from app.api.timeline import router as timeline_router
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.observability_middleware import ObservabilityMiddleware
from app.services import ai_orchestrator
from app.services.observability import observability_tracker


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    observability_tracker.reset()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="BrewPilot API - Test")
    app.add_middleware(ObservabilityMiddleware)

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(recipe_router, prefix=settings.api_prefix)
    app.include_router(batch_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)
    app.include_router(inventory_router, prefix=settings.api_prefix)
    app.include_router(timeline_router, prefix=settings.api_prefix)
    app.include_router(notifications_router, prefix=settings.api_prefix)
    app.include_router(observability_router, prefix=settings.api_prefix)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    observability_tracker.reset()


def _register_and_get_headers(
    client: TestClient,
    username: str,
    email: str,
    password: str = "StrongPass123!",
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_recipe(client: TestClient, headers: dict[str, str]) -> int:
    payload = {
        "name": "Session IPA",
        "style": "21B",
        "target_og": 1.045,
        "target_fg": 1.010,
        "target_ibu": 40,
        "target_srm": 5,
        "efficiency_pct": 72,
        "notes": "Integration test recipe",
        "ingredients": [
            {
                "name": "Pale Malt",
                "ingredient_type": "grain",
                "amount": 4.3,
                "unit": "kg",
                "stage": "mash",
                "minute_added": 0,
            },
            {
                "name": "Citra",
                "ingredient_type": "hop",
                "amount": 40,
                "unit": "g",
                "stage": "boil",
                "minute_added": 10,
            },
            {
                "name": "US-05",
                "ingredient_type": "yeast",
                "amount": 1,
                "unit": "pack",
                "stage": "fermentation",
                "minute_added": 0,
            },
        ],
    }
    response = client.post("/api/v1/recipes", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


def _create_batch(client: TestClient, headers: dict[str, str], recipe_id: int, name: str, status: str = "fermenting") -> int:
    response = client.post(
        "/api/v1/batches",
        json={
            "recipe_id": recipe_id,
            "name": name,
            "brewed_on": "2026-02-25",
            "status": status,
            "volume_liters": 20.0,
            "measured_og": 1.045,
            "notes": "Brew day started",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_inventory_item(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    ingredient_type: str,
    quantity: float,
    unit: str,
    low_stock_threshold: float,
) -> int:
    response = client.post(
        "/api/v1/inventory",
        json={
            "name": name,
            "ingredient_type": ingredient_type,
            "quantity": quantity,
            "unit": unit,
            "low_stock_threshold": low_stock_threshold,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_brew_step(
    client: TestClient,
    headers: dict[str, str],
    *,
    batch_id: int,
    step_order: int,
    name: str,
    scheduled_for: str | None = None,
    status: str = "pending",
) -> int:
    payload: dict[str, object] = {
        "step_order": step_order,
        "name": name,
        "description": "integration test step",
        "duration_minutes": 15,
        "status": status,
    }
    if scheduled_for is not None:
        payload["scheduled_for"] = scheduled_for

    response = client.post(
        f"/api/v1/batches/{batch_id}/timeline/steps",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_register_login_and_me(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "StrongPass123!",
        },
    )
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body["token_type"] == "bearer"
    assert register_body["user"]["username"] == "alice"

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "alice@example.com",
            "password": "StrongPass123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "alice@example.com"


def test_protected_endpoints_require_auth(client: TestClient) -> None:
    assert client.get("/api/v1/recipes").status_code == 401
    assert client.get("/api/v1/inventory").status_code == 401
    assert client.get("/api/v1/notifications/upcoming-steps").status_code == 401
    assert client.get("/api/v1/observability/metrics").status_code == 401

    create_response = client.post(
        "/api/v1/recipes",
        json={
            "name": "Unauthorized",
            "style": "21B",
            "target_og": 1.050,
            "target_fg": 1.011,
            "target_ibu": 35,
            "target_srm": 6,
            "efficiency_pct": 70,
            "notes": "Should fail",
            "ingredients": [],
        },
    )
    assert create_response.status_code == 401


def test_observability_metrics_endpoint(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="metrics-user", email="metrics-user@example.com")
    _ = _create_recipe(client, headers=headers)
    _ = client.get("/api/v1/recipes", headers=headers)

    metrics_response = client.get("/api/v1/observability/metrics", headers=headers)
    assert metrics_response.status_code == 200
    body = metrics_response.json()

    assert body["total_requests"] >= 3
    assert "generated_at" in body
    assert "uptime_seconds" in body

    route_keys = {(item["method"], item["path"]) for item in body["routes"]}
    assert ("POST", "/api/v1/recipes") in route_keys
    assert ("GET", "/api/v1/recipes") in route_keys


def test_observability_tracks_server_errors(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _register_and_get_headers(client, username="error-user", email="error-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)

    def explode(*args: object, **kwargs: object) -> object:
        raise RuntimeError("forced failure")

    monkeypatch.setattr(ai_orchestrator, "optimize_recipe", explode)

    response = client.post(
        "/api/v1/ai/recipe-optimize",
        json={
            "recipe_id": recipe_id,
            "measured_og": 1.038,
            "measured_fg": 1.016,
        },
        headers=headers,
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    assert response.json().get("request_id")

    metrics_response = client.get("/api/v1/observability/metrics", headers=headers)
    assert metrics_response.status_code == 200
    body = metrics_response.json()
    assert body["total_server_errors"] >= 1


def test_recipe_flow_and_ai_optimize(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="brewer1", email="brewer1@example.com")
    recipe_id = _create_recipe(client, headers=headers)

    list_response = client.get("/api/v1/recipes", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/v1/recipes/{recipe_id}", headers=headers)
    assert get_response.status_code == 200
    recipe = get_response.json()
    assert recipe["name"] == "Session IPA"
    assert len(recipe["ingredients"]) == 3

    optimize_response = client.post(
        "/api/v1/ai/recipe-optimize",
        json={
            "recipe_id": recipe_id,
            "measured_og": 1.038,
            "measured_fg": 1.016,
        },
        headers=headers,
    )
    assert optimize_response.status_code == 200
    body = optimize_response.json()
    assert body["summary"].startswith("Generated ")

    titles = {item["title"] for item in body["suggestions"]}
    assert "Raise mash efficiency" in titles
    assert "Improve attenuation" in titles
    assert body["source"] in {"rules", "llm", "llm_fallback"}


def test_batch_readings_and_ai_diagnose(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="brewer2", email="brewer2@example.com")
    recipe_id = _create_recipe(client, headers=headers)
    batch_id = _create_batch(client, headers, recipe_id, "Session IPA Batch 1")

    first_reading = client.post(
        f"/api/v1/batches/{batch_id}/readings",
        json={"gravity": 1.0400, "temp_c": 23.0, "ph": 5.10, "notes": "Day 2"},
        headers=headers,
    )
    assert first_reading.status_code == 201

    second_reading = client.post(
        f"/api/v1/batches/{batch_id}/readings",
        json={"gravity": 1.0398, "temp_c": 25.0, "ph": 5.20, "notes": "Day 3"},
        headers=headers,
    )
    assert second_reading.status_code == 201

    diagnose_response = client.post(
        "/api/v1/ai/fermentation-diagnose",
        json={"batch_id": batch_id},
        headers=headers,
    )
    assert diagnose_response.status_code == 200
    body = diagnose_response.json()
    titles = {item["title"] for item in body["suggestions"]}
    assert "Potential stalled fermentation" in titles
    assert "Fermentation temperature high" in titles
    assert "pH trend check" in titles
    assert body["source"] in {"rules", "llm", "llm_fallback"}


def test_inventory_crud_and_low_stock_alerts(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="inventory-user", email="inventory-user@example.com")

    low_item_id = _create_inventory_item(
        client,
        headers,
        name="US-05",
        ingredient_type="yeast",
        quantity=1,
        unit="pack",
        low_stock_threshold=2,
    )
    healthy_item_id = _create_inventory_item(
        client,
        headers,
        name="Citra",
        ingredient_type="hop",
        quantity=200,
        unit="g",
        low_stock_threshold=50,
    )

    list_response = client.get("/api/v1/inventory", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2

    low_stock_only = client.get("/api/v1/inventory?low_stock_only=true", headers=headers)
    assert low_stock_only.status_code == 200
    assert len(low_stock_only.json()) == 1
    assert low_stock_only.json()[0]["id"] == low_item_id

    alerts_response = client.get("/api/v1/inventory/alerts/low-stock", headers=headers)
    assert alerts_response.status_code == 200
    assert alerts_response.json()["count"] == 1
    assert alerts_response.json()["items"][0]["name"] == "US-05"

    get_item = client.get(f"/api/v1/inventory/{low_item_id}", headers=headers)
    assert get_item.status_code == 200
    assert get_item.json()["is_low_stock"] is True

    update_item = client.put(
        f"/api/v1/inventory/{low_item_id}",
        json={
            "name": "US-05",
            "ingredient_type": "yeast",
            "quantity": 3,
            "unit": "pack",
            "low_stock_threshold": 2,
        },
        headers=headers,
    )
    assert update_item.status_code == 200
    assert update_item.json()["is_low_stock"] is False

    alerts_after_update = client.get("/api/v1/inventory/alerts/low-stock", headers=headers)
    assert alerts_after_update.status_code == 200
    assert alerts_after_update.json()["count"] == 0

    delete_item = client.delete(f"/api/v1/inventory/{healthy_item_id}", headers=headers)
    assert delete_item.status_code == 204
    assert client.get(f"/api/v1/inventory/{healthy_item_id}", headers=headers).status_code == 404


def test_timeline_and_upcoming_notifications(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="timeline-user", email="timeline-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)
    batch_id = _create_batch(client, headers, recipe_id, "Timeline Batch", status="brewing")

    soon_time = (datetime.utcnow() + timedelta(minutes=20)).replace(microsecond=0).isoformat()
    later_time = (datetime.utcnow() + timedelta(minutes=180)).replace(microsecond=0).isoformat()

    step_a_id = _create_brew_step(
        client,
        headers,
        batch_id=batch_id,
        step_order=1,
        name="Heat strike water",
        scheduled_for=soon_time,
    )
    step_b_id = _create_brew_step(
        client,
        headers,
        batch_id=batch_id,
        step_order=2,
        name="Mash in",
        scheduled_for=later_time,
    )

    list_steps = client.get(f"/api/v1/batches/{batch_id}/timeline/steps", headers=headers)
    assert list_steps.status_code == 200
    assert [step["id"] for step in list_steps.json()] == [step_a_id, step_b_id]

    upcoming_60 = client.get("/api/v1/notifications/upcoming-steps?window_minutes=60", headers=headers)
    assert upcoming_60.status_code == 200
    body_60 = upcoming_60.json()
    assert body_60["count"] == 1
    assert body_60["steps"][0]["id"] == step_a_id
    assert body_60["steps"][0]["batch_id"] == batch_id

    complete_step = client.patch(
        f"/api/v1/batches/{batch_id}/timeline/steps/{step_a_id}",
        json={"status": "completed"},
        headers=headers,
    )
    assert complete_step.status_code == 200
    assert complete_step.json()["completed_at"] is not None

    upcoming_after_complete = client.get(
        "/api/v1/notifications/upcoming-steps?window_minutes=60",
        headers=headers,
    )
    assert upcoming_after_complete.status_code == 200
    assert upcoming_after_complete.json()["count"] == 0


def test_user_scope_isolation(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="owner-a", email="owner-a@example.com")
    headers_b = _register_and_get_headers(client, username="owner-b", email="owner-b@example.com")

    recipe_id = _create_recipe(client, headers=headers_a)
    batch_id = _create_batch(client, headers_a, recipe_id, "Owner A Batch", status="brewing")
    inventory_id = _create_inventory_item(
        client,
        headers_a,
        name="Citra",
        ingredient_type="hop",
        quantity=120,
        unit="g",
        low_stock_threshold=60,
    )
    step_id = _create_brew_step(
        client,
        headers_a,
        batch_id=batch_id,
        step_order=1,
        name="Owner A Step",
        scheduled_for=(datetime.utcnow() + timedelta(minutes=30)).replace(microsecond=0).isoformat(),
    )

    assert client.get("/api/v1/recipes", headers=headers_b).json() == []
    assert client.get(f"/api/v1/recipes/{recipe_id}", headers=headers_b).status_code == 404

    batch_b = client.post(
        "/api/v1/batches",
        json={
            "recipe_id": recipe_id,
            "name": "Blocked Batch",
            "brewed_on": "2026-02-25",
            "status": "planned",
            "volume_liters": 20,
            "notes": "Should not create",
        },
        headers=headers_b,
    )
    assert batch_b.status_code == 404

    assert client.get("/api/v1/inventory", headers=headers_b).json() == []
    assert client.get(f"/api/v1/inventory/{inventory_id}", headers=headers_b).status_code == 404

    same_name_for_b = client.post(
        "/api/v1/inventory",
        json={
            "name": "Citra",
            "ingredient_type": "hop",
            "quantity": 80,
            "unit": "g",
            "low_stock_threshold": 40,
        },
        headers=headers_b,
    )
    assert same_name_for_b.status_code == 201

    assert client.get(f"/api/v1/batches/{batch_id}/timeline/steps", headers=headers_b).status_code == 404
    assert (
        client.patch(
            f"/api/v1/batches/{batch_id}/timeline/steps/{step_id}",
            json={"status": "completed"},
            headers=headers_b,
        ).status_code
        == 404
    )
    assert client.get("/api/v1/notifications/upcoming-steps", headers=headers_b).json()["count"] == 0


def test_not_found_cases(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="brewer3", email="brewer3@example.com")

    assert client.get("/api/v1/recipes/9999", headers=headers).status_code == 404

    missing_batch_for_reading = client.post(
        "/api/v1/batches/9999/readings",
        json={"gravity": 1.020, "temp_c": 20.0, "ph": 4.4, "notes": "missing batch"},
        headers=headers,
    )
    assert missing_batch_for_reading.status_code == 404

    missing_recipe_optimize = client.post(
        "/api/v1/ai/recipe-optimize",
        json={"recipe_id": 9999, "measured_og": 1.050},
        headers=headers,
    )
    assert missing_recipe_optimize.status_code == 404

    missing_batch_diagnose = client.post(
        "/api/v1/ai/fermentation-diagnose",
        json={"batch_id": 9999},
        headers=headers,
    )
    assert missing_batch_diagnose.status_code == 404

    assert client.get("/api/v1/inventory/9999", headers=headers).status_code == 404
    assert client.get("/api/v1/batches/9999/timeline/steps", headers=headers).status_code == 404
