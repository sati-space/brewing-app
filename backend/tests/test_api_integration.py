from collections.abc import Generator

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
from app.api.recipes import router as recipe_router
from app.core.config import settings
from app.core.database import Base, get_db


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="BrewPilot API - Test")
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(recipe_router, prefix=settings.api_prefix)
    app.include_router(batch_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)

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
    list_response = client.get("/api/v1/recipes")
    assert list_response.status_code == 401

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


def test_batch_readings_and_ai_diagnose(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="brewer2", email="brewer2@example.com")
    recipe_id = _create_recipe(client, headers=headers)

    batch_response = client.post(
        "/api/v1/batches",
        json={
            "recipe_id": recipe_id,
            "name": "Session IPA Batch 1",
            "brewed_on": "2026-02-25",
            "status": "fermenting",
            "volume_liters": 20.0,
            "measured_og": 1.045,
            "notes": "Brew day complete",
        },
        headers=headers,
    )
    assert batch_response.status_code == 201
    batch_id = batch_response.json()["id"]

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


def test_user_scope_isolation(client: TestClient) -> None:
    headers_a = _register_and_get_headers(client, username="owner-a", email="owner-a@example.com")
    headers_b = _register_and_get_headers(client, username="owner-b", email="owner-b@example.com")

    recipe_id = _create_recipe(client, headers=headers_a)

    list_b = client.get("/api/v1/recipes", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json() == []

    get_b = client.get(f"/api/v1/recipes/{recipe_id}", headers=headers_b)
    assert get_b.status_code == 404

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


def test_not_found_cases(client: TestClient) -> None:
    headers = _register_and_get_headers(client, username="brewer3", email="brewer3@example.com")

    missing_recipe = client.get("/api/v1/recipes/9999", headers=headers)
    assert missing_recipe.status_code == 404

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
