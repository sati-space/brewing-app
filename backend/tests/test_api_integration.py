from collections.abc import Generator
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.ai import router as ai_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.batches import router as batch_router
from app.api.equipment import router as equipment_router
from app.api.health import router as health_router
from app.api.imports import router as imports_router
from app.api.ingredients import router as ingredients_router
from app.api.inventory import router as inventory_router
from app.api.notifications import router as notifications_router
from app.api.observability import router as observability_router
from app.api.recipes import router as recipe_router
from app.api.styles import router as styles_router
from app.api.timeline import router as timeline_router
from app.api.water_profiles import router as water_profiles_router
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
    app.include_router(styles_router, prefix=settings.api_prefix)
    app.include_router(batch_router, prefix=settings.api_prefix)
    app.include_router(analytics_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)
    app.include_router(imports_router, prefix=settings.api_prefix)
    app.include_router(ingredients_router, prefix=settings.api_prefix)
    app.include_router(equipment_router, prefix=settings.api_prefix)
    app.include_router(inventory_router, prefix=settings.api_prefix)
    app.include_router(timeline_router, prefix=settings.api_prefix)
    app.include_router(notifications_router, prefix=settings.api_prefix)
    app.include_router(observability_router, prefix=settings.api_prefix)
    app.include_router(water_profiles_router, prefix=settings.api_prefix)

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
    assert client.get("/api/v1/analytics/overview").status_code == 401
    assert client.get("/api/v1/imports/recipes/catalog").status_code == 401
    assert client.post("/api/v1/imports/recipes/import").status_code == 401
    assert client.get("/api/v1/styles/bjcp").status_code == 401
    assert client.get("/api/v1/styles/bjcp/21A").status_code == 401
    assert client.get("/api/v1/imports/ingredients/catalog").status_code == 401
    assert client.post("/api/v1/imports/ingredients/import").status_code == 401
    assert client.get("/api/v1/ingredients").status_code == 401
    assert client.post("/api/v1/ingredients").status_code == 401
    assert client.post("/api/v1/recipes/1/scale").status_code == 401
    assert client.post("/api/v1/recipes/1/hop-substitutions").status_code == 401
    assert client.get("/api/v1/water-profiles").status_code == 401
    assert client.post("/api/v1/water-profiles").status_code == 401
    assert client.post("/api/v1/water-profiles/1/recommendations").status_code == 401
    assert client.get("/api/v1/equipment").status_code == 401
    assert client.post("/api/v1/equipment").status_code == 401
    assert client.get("/api/v1/batches/1/recipe-snapshot").status_code == 401
    assert client.get("/api/v1/batches/1/inventory/preview").status_code == 401
    assert client.post("/api/v1/batches/1/inventory/consume").status_code == 401
    assert client.post("/api/v1/batches/1/brew-plan").status_code == 401
    assert client.get("/api/v1/batches/1/fermentation/trend").status_code == 401

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

    assert client.get(f"/api/v1/batches/{batch_id}/recipe-snapshot", headers=headers_b).status_code == 404
    assert client.get(f"/api/v1/batches/{batch_id}/inventory/preview", headers=headers_b).status_code == 404
    assert client.post(f"/api/v1/batches/{batch_id}/inventory/consume", headers=headers_b).status_code == 404
    assert client.get(f"/api/v1/batches/{batch_id}/readings", headers=headers_b).status_code == 404
    assert client.get(f"/api/v1/batches/{batch_id}/fermentation/trend", headers=headers_b).status_code == 404
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

    missing_recipe_scale = client.post(
        "/api/v1/recipes/9999/scale",
        json={"source_batch_volume_liters": 20, "target_batch_volume_liters": 25},
        headers=headers,
    )
    assert missing_recipe_scale.status_code == 404

    missing_hop_substitutions = client.post(
        "/api/v1/recipes/9999/hop-substitutions",
        json={"target_hop_name": "Citra", "available_hop_names": ["Mosaic"]},
        headers=headers,
    )
    assert missing_hop_substitutions.status_code == 404

    missing_water_profile = client.get("/api/v1/water-profiles/9999", headers=headers)
    assert missing_water_profile.status_code == 404

    missing_water_recommendation = client.post(
        "/api/v1/water-profiles/9999/recommendations",
        json={"style_code": "21A", "batch_volume_liters": 20},
        headers=headers,
    )
    assert missing_water_recommendation.status_code == 404

    missing_style = client.get("/api/v1/styles/bjcp/unknown", headers=headers)
    assert missing_style.status_code == 404

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
    assert client.get("/api/v1/ingredients/9999", headers=headers).status_code == 404
    assert client.get("/api/v1/equipment/9999", headers=headers).status_code == 404
    assert client.get("/api/v1/batches/9999/recipe-snapshot", headers=headers).status_code == 404
    assert client.get("/api/v1/batches/9999/inventory/preview", headers=headers).status_code == 404
    assert client.post("/api/v1/batches/9999/inventory/consume", headers=headers).status_code == 404
    assert client.post("/api/v1/batches/9999/brew-plan", headers=headers).status_code == 404
    assert client.get("/api/v1/batches/9999/readings", headers=headers).status_code == 404
    assert client.get("/api/v1/batches/9999/fermentation/trend", headers=headers).status_code == 404
    assert client.get("/api/v1/batches/9999/timeline/steps", headers=headers).status_code == 404


def test_analytics_overview_defaults_when_empty(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="analytics-empty", email="analytics-empty@example.com")

    response = client.get("/api/v1/analytics/overview", headers=headers)
    assert response.status_code == 200

    body = response.json()
    assert body["total_recipes"] == 0
    assert body["total_batches"] == 0
    assert body["completed_batches"] == 0
    assert body["average_abv"] is None
    assert body["average_attenuation_pct"] is None
    assert body["style_breakdown"] == []
    assert body["recent_batches"] == []


def test_analytics_overview_user_scoped_metrics(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="analytics-a", email="analytics-a@example.com")
    headers_b = _register_and_get_headers(client, username="analytics-b", email="analytics-b@example.com")

    recipe_a_ipa = client.post(
        "/api/v1/recipes",
        json={
            "name": "A IPA",
            "style": "IPA",
            "target_og": 1.050,
            "target_fg": 1.011,
            "target_ibu": 45,
            "target_srm": 6,
            "efficiency_pct": 74,
            "notes": "",
            "ingredients": [],
        },
        headers=headers_a,
    )
    assert recipe_a_ipa.status_code == 201
    recipe_a_ipa_id = recipe_a_ipa.json()["id"]

    recipe_a_stout = client.post(
        "/api/v1/recipes",
        json={
            "name": "A Stout",
            "style": "Stout",
            "target_og": 1.060,
            "target_fg": 1.016,
            "target_ibu": 35,
            "target_srm": 30,
            "efficiency_pct": 70,
            "notes": "",
            "ingredients": [],
        },
        headers=headers_a,
    )
    assert recipe_a_stout.status_code == 201
    recipe_a_stout_id = recipe_a_stout.json()["id"]

    batch_a_1 = client.post(
        "/api/v1/batches",
        json={
            "recipe_id": recipe_a_ipa_id,
            "name": "A Batch IPA 1",
            "brewed_on": "2026-02-20",
            "status": "completed",
            "volume_liters": 20.0,
            "measured_og": 1.050,
            "measured_fg": 1.010,
            "notes": "",
        },
        headers=headers_a,
    )
    assert batch_a_1.status_code == 201

    batch_a_2 = client.post(
        "/api/v1/batches",
        json={
            "recipe_id": recipe_a_stout_id,
            "name": "A Batch Stout",
            "brewed_on": "2026-02-21",
            "status": "packaged",
            "volume_liters": 19.0,
            "measured_og": 1.060,
            "measured_fg": 1.015,
            "notes": "",
        },
        headers=headers_a,
    )
    assert batch_a_2.status_code == 201

    batch_a_3 = client.post(
        "/api/v1/batches",
        json={
            "recipe_id": recipe_a_ipa_id,
            "name": "A Batch IPA 2",
            "brewed_on": "2026-02-22",
            "status": "fermenting",
            "volume_liters": 20.0,
            "measured_og": 1.048,
            "notes": "",
        },
        headers=headers_a,
    )
    assert batch_a_3.status_code == 201

    recipe_b = client.post(
        "/api/v1/recipes",
        json={
            "name": "B Lager",
            "style": "Lager",
            "target_og": 1.047,
            "target_fg": 1.010,
            "target_ibu": 22,
            "target_srm": 4,
            "efficiency_pct": 68,
            "notes": "",
            "ingredients": [],
        },
        headers=headers_b,
    )
    assert recipe_b.status_code == 201
    recipe_b_id = recipe_b.json()["id"]

    batch_b = client.post(
        "/api/v1/batches",
        json={
            "recipe_id": recipe_b_id,
            "name": "B Batch",
            "brewed_on": "2026-02-23",
            "status": "completed",
            "volume_liters": 20.0,
            "measured_og": 1.047,
            "measured_fg": 1.011,
            "notes": "",
        },
        headers=headers_b,
    )
    assert batch_b.status_code == 201

    response = client.get("/api/v1/analytics/overview", headers=headers_a)
    assert response.status_code == 200
    body = response.json()

    assert body["total_recipes"] == 2
    assert body["total_batches"] == 3
    assert body["completed_batches"] == 2
    assert body["average_abv"] == 5.58
    assert body["average_attenuation_pct"] == 77.5

    style_counts = {item["style"]: item["batch_count"] for item in body["style_breakdown"]}
    assert style_counts == {"IPA": 2, "Stout": 1}

    recent_names = [item["name"] for item in body["recent_batches"]]
    assert recent_names == ["A Batch IPA 2", "A Batch Stout", "A Batch IPA 1"]


def test_fermentation_trend_alerts_and_readings_order(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="trend-user", email="trend-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)
    batch_id = _create_batch(client, headers, recipe_id, "Trend Batch", status="fermenting")

    reading_payloads = [
        {"recorded_at": "2026-02-20T08:00:00", "gravity": 1.0500, "temp_c": 20.0, "ph": 5.2, "notes": "Day 0"},
        {"recorded_at": "2026-02-22T08:00:00", "gravity": 1.0320, "temp_c": 21.0, "ph": 5.0, "notes": "Day 2"},
        {"recorded_at": "2026-02-23T08:00:00", "gravity": 1.0310, "temp_c": 24.8, "ph": 4.9, "notes": "Day 3"},
        {"recorded_at": "2026-02-23T20:00:00", "gravity": 1.0308, "temp_c": 25.2, "ph": 4.8, "notes": "Day 3 PM"},
    ]

    for payload in reading_payloads:
        response = client.post(
            f"/api/v1/batches/{batch_id}/readings",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201

    list_response = client.get(f"/api/v1/batches/{batch_id}/readings", headers=headers)
    assert list_response.status_code == 200
    listed = list_response.json()
    assert [item["gravity"] for item in listed] == [1.05, 1.032, 1.031, 1.0308]

    trend_response = client.get(f"/api/v1/batches/{batch_id}/fermentation/trend", headers=headers)
    assert trend_response.status_code == 200
    body = trend_response.json()

    assert body["batch_id"] == batch_id
    assert body["reading_count"] == 4
    assert body["first_recorded_at"].startswith("2026-02-20T08:00:00")
    assert body["latest_recorded_at"].startswith("2026-02-23T20:00:00")
    assert body["latest_gravity"] == 1.0308
    assert body["latest_temp_c"] == 25.2
    assert body["latest_ph"] == 4.8
    assert body["gravity_drop"] == 0.0192
    assert body["average_hourly_gravity_drop"] == 0.00023
    assert body["plateau_risk"] is True
    assert body["temperature_warning"] is True

    assert any("flattened" in alert for alert in body["alerts"])
    assert any("temperature is high" in alert for alert in body["alerts"])

    trend_points = body["readings"]
    assert len(trend_points) == 4
    assert trend_points[-1]["gravity"] == 1.0308


def test_batch_recipe_snapshot_returns_frozen_recipe_data(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="snapshot-user", email="snapshot-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)
    batch_id = _create_batch(client, headers, recipe_id, "Snapshot Batch", status="brewing")

    response = client.get(f"/api/v1/batches/{batch_id}/recipe-snapshot", headers=headers)
    assert response.status_code == 200

    body = response.json()
    assert body["batch_id"] == batch_id
    assert body["recipe_id"] == recipe_id
    assert body["captured_at"] is not None
    assert body["name"] == "Session IPA"
    assert body["style"] == "21B"
    assert body["target_og"] == 1.045
    assert body["target_fg"] == 1.01
    assert body["target_ibu"] == 40.0
    assert body["target_srm"] == 5.0
    assert body["efficiency_pct"] == 72.0

    ingredient_names = [ingredient["name"] for ingredient in body["ingredients"]]
    assert ingredient_names == ["Pale Malt", "Citra", "US-05"]


def test_batch_inventory_preview_and_consume_flow(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="consume-user", email="consume-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)
    batch_id = _create_batch(client, headers, recipe_id, "Consume Batch", status="brewing")

    _create_inventory_item(
        client,
        headers,
        name="Pale Malt",
        ingredient_type="grain",
        quantity=5000,
        unit="g",
        low_stock_threshold=1000,
    )
    _create_inventory_item(
        client,
        headers,
        name="Citra",
        ingredient_type="hop",
        quantity=0.1,
        unit="kg",
        low_stock_threshold=0.02,
    )
    _create_inventory_item(
        client,
        headers,
        name="US-05",
        ingredient_type="yeast",
        quantity=2,
        unit="pack",
        low_stock_threshold=1,
    )

    preview_response = client.get(f"/api/v1/batches/{batch_id}/inventory/preview", headers=headers)
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["can_consume"] is True
    assert preview["shortage_count"] == 0
    assert len(preview["requirements"]) == 3

    preview_by_name = {row["name"]: row for row in preview["requirements"]}
    assert preview_by_name["Pale Malt"]["available_amount"] == 5.0
    assert preview_by_name["Citra"]["available_amount"] == 100.0
    assert preview_by_name["US-05"]["available_amount"] == 2.0

    consume_response = client.post(f"/api/v1/batches/{batch_id}/inventory/consume", headers=headers)
    assert consume_response.status_code == 200
    consume = consume_response.json()
    assert consume["consumed"] is True
    assert consume["shortage_count"] == 0
    assert consume["consumed_at"] is not None
    assert len(consume["items"]) == 3

    inventory_after = client.get("/api/v1/inventory", headers=headers)
    assert inventory_after.status_code == 200
    items_after = {item["name"]: item for item in inventory_after.json()}
    assert items_after["Pale Malt"]["quantity"] == 700.0
    assert items_after["Citra"]["quantity"] == pytest.approx(0.06, abs=1e-6)
    assert items_after["US-05"]["quantity"] == 1.0

    second_consume = client.post(f"/api/v1/batches/{batch_id}/inventory/consume", headers=headers)
    assert second_consume.status_code == 409
    second_body = second_consume.json()["detail"]
    assert second_body["consumed"] is False
    assert second_body["detail"] == "Inventory already consumed for this batch."



def test_batch_inventory_consume_returns_shortages(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="shortage-user", email="shortage-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)
    batch_id = _create_batch(client, headers, recipe_id, "Shortage Batch", status="brewing")

    _create_inventory_item(
        client,
        headers,
        name="Citra",
        ingredient_type="hop",
        quantity=20,
        unit="g",
        low_stock_threshold=10,
    )

    preview_response = client.get(f"/api/v1/batches/{batch_id}/inventory/preview", headers=headers)
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["can_consume"] is False
    assert preview["shortage_count"] == 3

    consume_response = client.post(f"/api/v1/batches/{batch_id}/inventory/consume", headers=headers)
    assert consume_response.status_code == 409
    detail = consume_response.json()["detail"]
    assert detail["consumed"] is False
    assert detail["shortage_count"] == 3
    assert detail["detail"] == "Insufficient inventory to consume this batch."
    assert len(detail["shortages"]) == 3


def test_external_recipe_catalog_and_import_flow(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="import-recipe-user", email="import-recipe-user@example.com")

    catalog_response = client.get("/api/v1/imports/recipes/catalog", headers=headers)
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert catalog["count"] >= 1
    assert len(catalog["items"]) >= 1

    item = catalog["items"][0]

    import_response = client.post(
        "/api/v1/imports/recipes/import",
        json={"provider": item["provider"], "external_id": item["external_id"]},
        headers=headers,
    )
    assert import_response.status_code == 201
    imported = import_response.json()
    assert imported["provider"] == item["provider"]
    assert imported["external_id"] == item["external_id"]
    assert imported["recipe_name"] == item["name"]

    recipe_id = imported["recipe_id"]
    recipe_response = client.get(f"/api/v1/recipes/{recipe_id}", headers=headers)
    assert recipe_response.status_code == 200
    recipe = recipe_response.json()
    assert recipe["name"] == item["name"]
    assert recipe["style"] == item["style"]
    assert len(recipe["ingredients"]) == len(item["ingredients"])



def test_external_equipment_catalog_import_and_scope(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="import-equip-a", email="import-equip-a@example.com")
    headers_b = _register_and_get_headers(client, username="import-equip-b", email="import-equip-b@example.com")

    catalog_response = client.get("/api/v1/imports/equipment/catalog", headers=headers_a)
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert catalog["count"] >= 1

    item = catalog["items"][0]

    import_response = client.post(
        "/api/v1/imports/equipment/import",
        json={"provider": item["provider"], "external_id": item["external_id"]},
        headers=headers_a,
    )
    assert import_response.status_code == 201
    imported = import_response.json()
    equipment_id = imported["equipment_profile"]["id"]

    list_a = client.get("/api/v1/imports/equipment", headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1

    get_a = client.get(f"/api/v1/imports/equipment/{equipment_id}", headers=headers_a)
    assert get_a.status_code == 200
    assert get_a.json()["name"] == item["name"]

    list_b = client.get("/api/v1/imports/equipment", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json() == []

    get_b = client.get(f"/api/v1/imports/equipment/{equipment_id}", headers=headers_b)
    assert get_b.status_code == 404

    duplicate_import = client.post(
        "/api/v1/imports/equipment/import",
        json={"provider": item["provider"], "external_id": item["external_id"]},
        headers=headers_a,
    )
    assert duplicate_import.status_code == 409



def test_external_import_not_found_cases(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="import-missing", email="import-missing@example.com")

    missing_recipe = client.post(
        "/api/v1/imports/recipes/import",
        json={"provider": "missing", "external_id": "x"},
        headers=headers,
    )
    assert missing_recipe.status_code == 404

    missing_equipment = client.post(
        "/api/v1/imports/equipment/import",
        json={"provider": "missing", "external_id": "x"},
        headers=headers,
    )
    assert missing_equipment.status_code == 404

    missing_ingredient = client.post(
        "/api/v1/imports/ingredients/import",
        json={"provider": "missing", "external_id": "x"},
        headers=headers,
    )
    assert missing_ingredient.status_code == 404

    missing_equipment_profile = client.get("/api/v1/imports/equipment/9999", headers=headers)
    assert missing_equipment_profile.status_code == 404


def test_ingredients_crud_flow(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="ingredient-user", email="ingredient-user@example.com")

    create_response = client.post(
        "/api/v1/ingredients",
        json={
            "name": "Centennial",
            "ingredient_type": "hop",
            "default_unit": "g",
            "notes": "Citrus-forward hop",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    ingredient = create_response.json()
    ingredient_id = ingredient["id"]
    assert ingredient["name"] == "Centennial"

    duplicate_create = client.post(
        "/api/v1/ingredients",
        json={
            "name": "Centennial",
            "ingredient_type": "hop",
            "default_unit": "g",
            "notes": "Duplicate",
        },
        headers=headers,
    )
    assert duplicate_create.status_code == 409

    list_response = client.get("/api/v1/ingredients", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    filtered = client.get("/api/v1/ingredients?ingredient_type=hop&search=Cent", headers=headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    update_response = client.put(
        f"/api/v1/ingredients/{ingredient_id}",
        json={
            "name": "Centennial T90",
            "ingredient_type": "hop",
            "default_unit": "g",
            "notes": "Pellet hop",
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Centennial T90"

    get_response = client.get(f"/api/v1/ingredients/{ingredient_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["default_unit"] == "g"

    delete_response = client.delete(f"/api/v1/ingredients/{ingredient_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_after_delete = client.get(f"/api/v1/ingredients/{ingredient_id}", headers=headers)
    assert missing_after_delete.status_code == 404



def test_ingredients_user_scope_isolation(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="ingredient-owner-a", email="ingredient-owner-a@example.com")
    headers_b = _register_and_get_headers(client, username="ingredient-owner-b", email="ingredient-owner-b@example.com")

    create_response = client.post(
        "/api/v1/ingredients",
        json={
            "name": "Pilsner Malt",
            "ingredient_type": "grain",
            "default_unit": "kg",
            "notes": "Base malt",
        },
        headers=headers_a,
    )
    assert create_response.status_code == 201
    ingredient_id = create_response.json()["id"]

    assert client.get(f"/api/v1/ingredients/{ingredient_id}", headers=headers_b).status_code == 404
    assert client.put(
        f"/api/v1/ingredients/{ingredient_id}",
        json={
            "name": "Pilsner Malt",
            "ingredient_type": "grain",
            "default_unit": "kg",
            "notes": "attempt",
        },
        headers=headers_b,
    ).status_code == 404
    assert client.delete(f"/api/v1/ingredients/{ingredient_id}", headers=headers_b).status_code == 404



def test_external_ingredient_catalog_and_import_flow(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="ingredient-import-user", email="ingredient-import-user@example.com")

    catalog_response = client.get("/api/v1/imports/ingredients/catalog?ingredient_type=hop", headers=headers)
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert catalog["count"] >= 1
    assert all(item["ingredient_type"] == "hop" for item in catalog["items"])

    item = catalog["items"][0]

    import_response = client.post(
        "/api/v1/imports/ingredients/import",
        json={"provider": item["provider"], "external_id": item["external_id"]},
        headers=headers,
    )
    assert import_response.status_code == 201
    imported = import_response.json()
    assert imported["provider"] == item["provider"]
    assert imported["external_id"] == item["external_id"]
    assert imported["ingredient_profile"]["name"] == item["name"]

    ingredients_response = client.get("/api/v1/ingredients", headers=headers)
    assert ingredients_response.status_code == 200
    names = {profile["name"] for profile in ingredients_response.json()}
    assert item["name"] in names

    duplicate_import = client.post(
        "/api/v1/imports/ingredients/import",
        json={"provider": item["provider"], "external_id": item["external_id"]},
        headers=headers,
    )
    assert duplicate_import.status_code == 409


def test_equipment_crud_flow(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="equipment-user", email="equipment-user@example.com")

    create_response = client.post(
        "/api/v1/equipment",
        json={
            "name": "Garage BIAB",
            "batch_volume_liters": 25,
            "mash_tun_volume_liters": 35,
            "boil_kettle_volume_liters": 35,
            "brewhouse_efficiency_pct": 71,
            "boil_off_rate_l_per_hour": 3.0,
            "trub_loss_liters": 1.2,
            "notes": "single-vessel electric",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    equipment = create_response.json()
    equipment_id = equipment["id"]
    assert equipment["source_provider"] == "manual"

    duplicate = client.post(
        "/api/v1/equipment",
        json={
            "name": "Garage BIAB",
            "batch_volume_liters": 22,
            "mash_tun_volume_liters": 30,
            "boil_kettle_volume_liters": 30,
            "brewhouse_efficiency_pct": 68,
            "boil_off_rate_l_per_hour": 2.8,
            "trub_loss_liters": 1.0,
            "notes": "duplicate",
        },
        headers=headers,
    )
    assert duplicate.status_code == 409

    list_response = client.get("/api/v1/equipment?source_provider=manual&search=Garage", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/v1/equipment/{equipment_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Garage BIAB"

    update_response = client.put(
        f"/api/v1/equipment/{equipment_id}",
        json={
            "name": "Garage BIAB V2",
            "batch_volume_liters": 24,
            "mash_tun_volume_liters": 35,
            "boil_kettle_volume_liters": 35,
            "brewhouse_efficiency_pct": 73,
            "boil_off_rate_l_per_hour": 2.9,
            "trub_loss_liters": 1.1,
            "notes": "updated",
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Garage BIAB V2"

    delete_response = client.delete(f"/api/v1/equipment/{equipment_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_after_delete = client.get(f"/api/v1/equipment/{equipment_id}", headers=headers)
    assert missing_after_delete.status_code == 404



def test_equipment_user_scope_isolation_and_import_visibility(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="equipment-owner-a", email="equipment-owner-a@example.com")
    headers_b = _register_and_get_headers(client, username="equipment-owner-b", email="equipment-owner-b@example.com")

    manual_create = client.post(
        "/api/v1/equipment",
        json={
            "name": "Owner A Manual",
            "batch_volume_liters": 20,
            "mash_tun_volume_liters": 28,
            "boil_kettle_volume_liters": 35,
            "brewhouse_efficiency_pct": 70,
            "boil_off_rate_l_per_hour": 3.1,
            "trub_loss_liters": 1.3,
            "notes": "manual",
        },
        headers=headers_a,
    )
    assert manual_create.status_code == 201
    manual_id = manual_create.json()["id"]

    import_catalog = client.get("/api/v1/imports/equipment/catalog", headers=headers_a)
    assert import_catalog.status_code == 200
    item = import_catalog.json()["items"][0]

    import_response = client.post(
        "/api/v1/imports/equipment/import",
        json={"provider": item["provider"], "external_id": item["external_id"]},
        headers=headers_a,
    )
    assert import_response.status_code == 201
    imported_id = import_response.json()["equipment_profile"]["id"]

    list_a = client.get("/api/v1/equipment", headers=headers_a)
    assert list_a.status_code == 200
    ids_a = {entry["id"] for entry in list_a.json()}
    assert manual_id in ids_a
    assert imported_id in ids_a

    list_b = client.get("/api/v1/equipment", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json() == []

    assert client.get(f"/api/v1/equipment/{manual_id}", headers=headers_b).status_code == 404
    assert client.get(f"/api/v1/equipment/{imported_id}", headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/equipment/{manual_id}", headers=headers_b).status_code == 404


def test_recipe_scale_with_manual_target_efficiency(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="scale-user", email="scale-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)

    scale_response = client.post(
        f"/api/v1/recipes/{recipe_id}/scale",
        json={
            "source_batch_volume_liters": 20,
            "target_batch_volume_liters": 25,
            "target_efficiency_pct": 78,
        },
        headers=headers,
    )
    assert scale_response.status_code == 200
    scaled = scale_response.json()

    assert scaled["recipe_id"] == recipe_id
    assert scaled["scale_factor"] == 1.25
    assert scaled["source_efficiency_pct"] == 72.0
    assert scaled["target_efficiency_pct"] == 78.0
    assert scaled["estimated_target_og"] == 1.049
    assert scaled["estimated_target_fg"] == 1.011

    by_name = {item["name"]: item for item in scaled["ingredients"]}
    assert by_name["Pale Malt"]["original_amount"] == 4.3
    assert by_name["Pale Malt"]["scaled_amount"] == 5.375
    assert by_name["Citra"]["scaled_amount"] == 50.0



def test_recipe_scale_uses_equipment_efficiency(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="scale-equip-user", email="scale-equip-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)

    equipment_response = client.post(
        "/api/v1/equipment",
        json={
            "name": "Scale Rig",
            "batch_volume_liters": 23,
            "mash_tun_volume_liters": 32,
            "boil_kettle_volume_liters": 38,
            "brewhouse_efficiency_pct": 68,
            "boil_off_rate_l_per_hour": 2.9,
            "trub_loss_liters": 1.1,
            "notes": "",
        },
        headers=headers,
    )
    assert equipment_response.status_code == 201
    equipment_id = equipment_response.json()["id"]

    scale_response = client.post(
        f"/api/v1/recipes/{recipe_id}/scale",
        json={
            "source_batch_volume_liters": 20,
            "target_batch_volume_liters": 23,
            "equipment_profile_id": equipment_id,
        },
        headers=headers,
    )
    assert scale_response.status_code == 200
    scaled = scale_response.json()

    assert scaled["target_efficiency_pct"] == 68.0
    assert scaled["scale_factor"] == 1.15
    assert scaled["estimated_target_og"] == 1.042



def test_recipe_scale_rejects_other_user_equipment(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="scale-owner-a", email="scale-owner-a@example.com")
    headers_b = _register_and_get_headers(client, username="scale-owner-b", email="scale-owner-b@example.com")

    recipe_id = _create_recipe(client, headers=headers_a)

    equipment_response = client.post(
        "/api/v1/equipment",
        json={
            "name": "Owner B Rig",
            "batch_volume_liters": 20,
            "mash_tun_volume_liters": 28,
            "boil_kettle_volume_liters": 35,
            "brewhouse_efficiency_pct": 70,
            "boil_off_rate_l_per_hour": 3.0,
            "trub_loss_liters": 1.2,
            "notes": "",
        },
        headers=headers_b,
    )
    assert equipment_response.status_code == 201
    equipment_id = equipment_response.json()["id"]

    scale_response = client.post(
        f"/api/v1/recipes/{recipe_id}/scale",
        json={
            "source_batch_volume_liters": 20,
            "target_batch_volume_liters": 25,
            "equipment_profile_id": equipment_id,
        },
        headers=headers_a,
    )
    assert scale_response.status_code == 404


def test_recipe_hop_substitutions_with_provided_candidates(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="hop-sub-user", email="hop-sub-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)

    response = client.post(
        f"/api/v1/recipes/{recipe_id}/hop-substitutions",
        json={
            "target_hop_name": "Citra",
            "available_hop_names": ["Mosaic", "Amarillo", "Unknown Experimental Hop"],
            "include_inventory_hops": False,
            "top_k": 3,
        },
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()

    assert body["recipe_id"] == recipe_id
    assert body["candidate_source"] == "provided"
    assert body["target_hop_profile"]["name"] == "Citra"
    assert body["recognized_candidate_count"] == 2
    assert "Unknown Experimental Hop" in body["unresolved_hop_names"]
    assert len(body["substitutions"]) == 2

    top = body["substitutions"][0]
    assert top["name"] == "Mosaic"
    assert top["similarity_score"] > 0.8
    assert "citrus" in top["shared_descriptors"]


def test_recipe_hop_substitutions_uses_inventory_candidates(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="hop-sub-inv", email="hop-sub-inv@example.com")
    recipe_id = _create_recipe(client, headers=headers)

    _create_inventory_item(
        client,
        headers,
        name="Simcoe",
        ingredient_type="hop",
        quantity=120,
        unit="g",
        low_stock_threshold=30,
    )
    _create_inventory_item(
        client,
        headers,
        name="Magnum",
        ingredient_type="hop",
        quantity=80,
        unit="g",
        low_stock_threshold=20,
    )
    _create_inventory_item(
        client,
        headers,
        name="Pale Malt",
        ingredient_type="grain",
        quantity=5,
        unit="kg",
        low_stock_threshold=1,
    )

    response = client.post(
        f"/api/v1/recipes/{recipe_id}/hop-substitutions",
        json={
            "target_hop_name": "Citra",
            "available_hop_names": [],
            "include_inventory_hops": True,
            "top_k": 5,
        },
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()

    assert body["candidate_source"] == "inventory"
    assert body["recognized_candidate_count"] == 2
    names = [item["name"] for item in body["substitutions"]]
    assert "Simcoe" in names
    assert "Magnum" in names


def test_recipe_hop_substitutions_requires_hop_from_recipe(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="hop-sub-validate", email="hop-sub-validate@example.com")
    recipe_id = _create_recipe(client, headers=headers)

    response = client.post(
        f"/api/v1/recipes/{recipe_id}/hop-substitutions",
        json={
            "target_hop_name": "Saaz",
            "available_hop_names": ["Hallertau"],
            "include_inventory_hops": False,
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Target hop is not present in this recipe."


def test_recipe_hop_substitutions_does_not_use_other_user_inventory(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="hop-sub-owner-a", email="hop-sub-owner-a@example.com")
    headers_b = _register_and_get_headers(client, username="hop-sub-owner-b", email="hop-sub-owner-b@example.com")
    recipe_id = _create_recipe(client, headers=headers_a)

    _create_inventory_item(
        client,
        headers_b,
        name="Mosaic",
        ingredient_type="hop",
        quantity=100,
        unit="g",
        low_stock_threshold=25,
    )

    response = client.post(
        f"/api/v1/recipes/{recipe_id}/hop-substitutions",
        json={
            "target_hop_name": "Citra",
            "available_hop_names": [],
            "include_inventory_hops": True,
        },
        headers=headers_a,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "No candidate hops found. Provide available_hop_names or add hop inventory."


def test_bjcp_style_catalog_and_detail(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="styles-user", email="styles-user@example.com")

    catalog_response = client.get("/api/v1/styles/bjcp?search=ipa", headers=headers)
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert catalog["count"] >= 2
    codes = {item["code"] for item in catalog["items"]}
    assert "21A" in codes

    detail_response = client.get("/api/v1/styles/bjcp/21A", headers=headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["name"] == "American IPA"
    assert detail["sulfate_ppm"]["target_ppm"] > detail["chloride_ppm"]["target_ppm"]


def test_water_profile_crud_and_recommendation_by_style_code(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="water-user", email="water-user@example.com")

    create_response = client.post(
        "/api/v1/water-profiles",
        json={
            "name": "My Tap Water",
            "calcium_ppm": 35,
            "magnesium_ppm": 8,
            "sodium_ppm": 12,
            "chloride_ppm": 30,
            "sulfate_ppm": 45,
            "bicarbonate_ppm": 60,
            "notes": "city profile",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    water_profile_id = create_response.json()["id"]

    duplicate_create = client.post(
        "/api/v1/water-profiles",
        json={
            "name": "My Tap Water",
            "calcium_ppm": 40,
            "magnesium_ppm": 8,
            "sodium_ppm": 12,
            "chloride_ppm": 30,
            "sulfate_ppm": 45,
            "bicarbonate_ppm": 60,
            "notes": "",
        },
        headers=headers,
    )
    assert duplicate_create.status_code == 409

    list_response = client.get("/api/v1/water-profiles?search=Tap", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    recommend_response = client.post(
        f"/api/v1/water-profiles/{water_profile_id}/recommendations",
        json={"style_code": "21A", "batch_volume_liters": 20},
        headers=headers,
    )
    assert recommend_response.status_code == 200
    recommendation = recommend_response.json()
    assert recommendation["style_code"] == "21A"
    assert recommendation["water_profile_id"] == water_profile_id
    assert len(recommendation["additions"]) >= 1
    mineral_names = {item["mineral_name"] for item in recommendation["additions"]}
    assert "Gypsum (CaSO4)" in mineral_names

    update_response = client.put(
        f"/api/v1/water-profiles/{water_profile_id}",
        json={
            "name": "My Tap Water V2",
            "calcium_ppm": 40,
            "magnesium_ppm": 10,
            "sodium_ppm": 12,
            "chloride_ppm": 35,
            "sulfate_ppm": 55,
            "bicarbonate_ppm": 65,
            "notes": "updated",
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "My Tap Water V2"

    delete_response = client.delete(f"/api/v1/water-profiles/{water_profile_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_after_delete = client.get(f"/api/v1/water-profiles/{water_profile_id}", headers=headers)
    assert missing_after_delete.status_code == 404


def test_water_recommendation_from_recipe_style(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="water-recipe-user", email="water-recipe-user@example.com")

    recipe_response = client.post(
        "/api/v1/recipes",
        json={
            "name": "American IPA Test",
            "style": "21A",
            "target_og": 1.062,
            "target_fg": 1.011,
            "target_ibu": 60,
            "target_srm": 7,
            "efficiency_pct": 72,
            "notes": "",
            "ingredients": [
                {
                    "name": "Citra",
                    "ingredient_type": "hop",
                    "amount": 40,
                    "unit": "g",
                    "stage": "boil",
                    "minute_added": 10,
                }
            ],
        },
        headers=headers,
    )
    assert recipe_response.status_code == 201
    recipe_id = recipe_response.json()["id"]

    water_response = client.post(
        "/api/v1/water-profiles",
        json={
            "name": "RO Blend",
            "calcium_ppm": 10,
            "magnesium_ppm": 2,
            "sodium_ppm": 3,
            "chloride_ppm": 8,
            "sulfate_ppm": 15,
            "bicarbonate_ppm": 20,
            "notes": "",
        },
        headers=headers,
    )
    assert water_response.status_code == 201
    water_profile_id = water_response.json()["id"]

    recommend_response = client.post(
        f"/api/v1/water-profiles/{water_profile_id}/recommendations",
        json={"recipe_id": recipe_id, "batch_volume_liters": 23},
        headers=headers,
    )
    assert recommend_response.status_code == 200
    body = recommend_response.json()
    assert body["style_code"] == "21A"
    assert body["batch_volume_liters"] == 23.0
    assert len(body["additions"]) >= 1


def test_water_profiles_user_scope_and_unknown_style(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="water-owner-a", email="water-owner-a@example.com")
    headers_b = _register_and_get_headers(client, username="water-owner-b", email="water-owner-b@example.com")

    water_response = client.post(
        "/api/v1/water-profiles",
        json={
            "name": "Owner A Water",
            "calcium_ppm": 25,
            "magnesium_ppm": 5,
            "sodium_ppm": 10,
            "chloride_ppm": 20,
            "sulfate_ppm": 30,
            "bicarbonate_ppm": 50,
            "notes": "",
        },
        headers=headers_a,
    )
    assert water_response.status_code == 201
    water_profile_id = water_response.json()["id"]

    assert client.get(f"/api/v1/water-profiles/{water_profile_id}", headers=headers_b).status_code == 404
    assert (
        client.post(
            f"/api/v1/water-profiles/{water_profile_id}/recommendations",
            json={"style_code": "21A"},
            headers=headers_b,
        ).status_code
        == 404
    )
    assert (
        client.put(
            f"/api/v1/water-profiles/{water_profile_id}",
            json={
                "name": "attempt",
                "calcium_ppm": 1,
                "magnesium_ppm": 1,
                "sodium_ppm": 1,
                "chloride_ppm": 1,
                "sulfate_ppm": 1,
                "bicarbonate_ppm": 1,
                "notes": "",
            },
            headers=headers_b,
        ).status_code
        == 404
    )

    unknown_style_response = client.post(
        f"/api/v1/water-profiles/{water_profile_id}/recommendations",
        json={"style_code": "not-a-style"},
        headers=headers_a,
    )
    assert unknown_style_response.status_code == 404

    missing_input_response = client.post(
        f"/api/v1/water-profiles/{water_profile_id}/recommendations",
        json={},
        headers=headers_a,
    )
    assert missing_input_response.status_code == 422
    assert missing_input_response.json()["detail"] == "Provide style_code or recipe_id for recommendation."


def test_brew_plan_combines_inventory_water_and_substitutions(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="brew-plan-user", email="brew-plan-user@example.com")
    recipe_id = _create_recipe(client, headers=headers)
    batch_id = _create_batch(client, headers, recipe_id, "Brew Plan Batch", status="planned")

    equipment_response = client.post(
        "/api/v1/equipment",
        json={
            "name": "Plan Rig",
            "batch_volume_liters": 20,
            "mash_tun_volume_liters": 25,
            "boil_kettle_volume_liters": 30,
            "brewhouse_efficiency_pct": 70,
            "boil_off_rate_l_per_hour": 3.2,
            "trub_loss_liters": 1.1,
            "notes": "",
        },
        headers=headers,
    )
    assert equipment_response.status_code == 201
    equipment_id = equipment_response.json()["id"]

    water_response = client.post(
        "/api/v1/water-profiles",
        json={
            "name": "Tap Plan Water",
            "calcium_ppm": 35,
            "magnesium_ppm": 6,
            "sodium_ppm": 12,
            "chloride_ppm": 30,
            "sulfate_ppm": 40,
            "bicarbonate_ppm": 55,
            "notes": "",
        },
        headers=headers,
    )
    assert water_response.status_code == 201
    water_profile_id = water_response.json()["id"]

    _create_inventory_item(
        client,
        headers,
        name="Pale Malt",
        ingredient_type="grain",
        quantity=2.0,
        unit="kg",
        low_stock_threshold=0.5,
    )
    _create_inventory_item(
        client,
        headers,
        name="US-05",
        ingredient_type="yeast",
        quantity=1.0,
        unit="pack",
        low_stock_threshold=0.2,
    )
    _create_inventory_item(
        client,
        headers,
        name="Mosaic",
        ingredient_type="hop",
        quantity=80.0,
        unit="g",
        low_stock_threshold=20.0,
    )

    brew_plan_response = client.post(
        f"/api/v1/batches/{batch_id}/brew-plan",
        json={
            "equipment_profile_id": equipment_id,
            "water_profile_id": water_profile_id,
            "available_hop_names": ["Simcoe"],
            "brew_start_at": "2026-03-01T08:00:00",
        },
        headers=headers,
    )
    assert brew_plan_response.status_code == 200
    body = brew_plan_response.json()

    assert body["batch_id"] == batch_id
    assert body["equipment"]["equipment_profile_id"] == equipment_id
    assert body["water_recommendation"] is not None
    assert body["water_recommendation"]["style_code"] == "21B"
    assert body["volumes"]["mash_target_temp_c"] > 60
    assert body["volumes"]["mash_rest_minutes"] >= 60
    assert body["gravity"]["estimated_og"] < body["gravity"]["source_target_og"]
    assert body["inventory_shortage_count"] >= 1

    shopping_names = {item["name"] for item in body["shopping_list"]}
    assert "Citra" in shopping_names

    hop_targets = {item["target_hop_name"] for item in body["hop_substitutions"]}
    assert "Citra" in hop_targets

    first_step = body["timer_plan"][0]
    assert first_step["start_offset_minutes"] == 0
    assert first_step["planned_start_at"].startswith("2026-03-01T08:00:00")


def test_brew_plan_scopes_profiles_to_owner(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="brew-plan-owner-a", email="brew-plan-owner-a@example.com")
    headers_b = _register_and_get_headers(client, username="brew-plan-owner-b", email="brew-plan-owner-b@example.com")

    recipe_id = _create_recipe(client, headers=headers_a)
    batch_id = _create_batch(client, headers_a, recipe_id, "Owner A Batch", status="planned")

    equipment_b = client.post(
        "/api/v1/equipment",
        json={
            "name": "Owner B Rig",
            "batch_volume_liters": 20,
            "mash_tun_volume_liters": 26,
            "boil_kettle_volume_liters": 31,
            "brewhouse_efficiency_pct": 69,
            "boil_off_rate_l_per_hour": 3.1,
            "trub_loss_liters": 1.0,
            "notes": "",
        },
        headers=headers_b,
    )
    assert equipment_b.status_code == 201
    equipment_id_b = equipment_b.json()["id"]

    water_b = client.post(
        "/api/v1/water-profiles",
        json={
            "name": "Owner B Water",
            "calcium_ppm": 30,
            "magnesium_ppm": 5,
            "sodium_ppm": 8,
            "chloride_ppm": 25,
            "sulfate_ppm": 35,
            "bicarbonate_ppm": 40,
            "notes": "",
        },
        headers=headers_b,
    )
    assert water_b.status_code == 201
    water_profile_id_b = water_b.json()["id"]

    invalid_equipment = client.post(
        f"/api/v1/batches/{batch_id}/brew-plan",
        json={"equipment_profile_id": equipment_id_b},
        headers=headers_a,
    )
    assert invalid_equipment.status_code == 404

    invalid_water = client.post(
        f"/api/v1/batches/{batch_id}/brew-plan",
        json={"water_profile_id": water_profile_id_b},
        headers=headers_a,
    )
    assert invalid_water.status_code == 404


def test_brew_plan_without_water_profile(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="brew-plan-nowater", email="brew-plan-nowater@example.com")
    recipe_id = _create_recipe(client, headers=headers)
    batch_id = _create_batch(client, headers, recipe_id, "No Water Batch", status="planned")

    _create_inventory_item(
        client,
        headers,
        name="Pale Malt",
        ingredient_type="grain",
        quantity=5.0,
        unit="kg",
        low_stock_threshold=1.0,
    )
    _create_inventory_item(
        client,
        headers,
        name="Citra",
        ingredient_type="hop",
        quantity=60.0,
        unit="g",
        low_stock_threshold=15.0,
    )
    _create_inventory_item(
        client,
        headers,
        name="US-05",
        ingredient_type="yeast",
        quantity=2.0,
        unit="pack",
        low_stock_threshold=1.0,
    )

    brew_plan_response = client.post(
        f"/api/v1/batches/{batch_id}/brew-plan",
        json={},
        headers=headers,
    )
    assert brew_plan_response.status_code == 200
    body = brew_plan_response.json()

    assert body["water_recommendation"] is None
    assert any("No water profile selected" in note for note in body["notes"])
    assert body["inventory_shortage_count"] == 0
