# BrewPilot

AI-first homebrewing and beer brewing platform focused on smooth UX, practical automation, and better brew outcomes.

This repo currently contains:

- A detailed MVP plan.
- A Python FastAPI backend scaffold.
- SQL schema + seed data.
- Integration tests for key API flows.
- Alembic migrations and PostgreSQL local setup.
- JWT auth and user-scoped API access.
- Inventory CRUD and low-stock alert endpoints.
- Brew day timeline and upcoming-step notification APIs.
- Optional LLM-backed AI suggestions with rule-based fallback.
- Observability middleware with request logs, error handling, and metrics.

## Why this stack

- **Python**: fast iteration for API + AI features.
- **SQL**: explicit schema for recipes, batches, fermentation, and inventory.
- **C# compatible**: API-first design so a future C# client (Blazor, MAUI, ASP.NET) can plug in cleanly.

## Project layout

```text
docs/
  mvp-spec.md
backend/
  alembic/
    versions/
  app/
    api/
    core/
    models/
    schemas/
    services/
  tests/
sql/
  schema.sql
  seed.sql
```

## Branch workflow

Use numbered feature branches and avoid direct commits to `main`.

Examples:

- `codex/ba-1`
- `codex/ba-2`
- `codex/ba-3`
- `codex/ba-4`
- `codex/ba-5`
- `codex/ba-6`
- `codex/ba-7`
- `codex/ba-8`
- `codex/ba-9`
- `codex/ba-10`
- `codex/ba-11`
- `codex/ba-12`
- `codex/ba-13`
- `codex/ba-14`
- `codex/ba-15`
- `codex/ba-16`
- `codex/ba-17`
- `codex/ba-18`

## Quick start (PostgreSQL + migrations)

```bash
# from repo root
docker compose up -d postgres

cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/v1/health`

## Auth endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

All recipe, batch, ingredient, imports, analytics, AI, inventory, timeline, notifications, and observability endpoints require `Authorization: Bearer <token>` except `GET /api/v1/health`.

## Recipe endpoints

- `POST /api/v1/recipes`
- `GET /api/v1/recipes`
- `GET /api/v1/recipes/{recipe_id}`
- `POST /api/v1/recipes/{recipe_id}/scale`
- `POST /api/v1/recipes/{recipe_id}/hop-substitutions`

`POST /api/v1/recipes/{recipe_id}/scale` returns scaled ingredient amounts and updated OG/FG estimates for target volume and efficiency.

`POST /api/v1/recipes/{recipe_id}/hop-substitutions` ranks substitute hops by flavor profile similarity and alpha-acid compatibility, using provided hop names and/or user inventory.

## AI endpoints

- `POST /api/v1/ai/recipe-optimize`
- `POST /api/v1/ai/fermentation-diagnose`

Response payloads include `source`:

- `rules` (deterministic rules engine)
- `llm` (LLM provider response)
- `llm_fallback` (LLM failed/unavailable, rules returned)

## LLM provider config

Set in `backend/.env`:

- `AI_PROVIDER`:
  - `rules` (default)
  - `llm` (enable provider calls)
- `AI_LLM_BASE_URL` (example: `https://api.openai.com`)
- `AI_LLM_API_KEY`
- `AI_LLM_MODEL`
- `AI_LLM_TIMEOUT_SECONDS`

The adapter uses an OpenAI-compatible `POST /v1/chat/completions` interface.

## Equipment endpoints

- `POST /api/v1/equipment`
- `GET /api/v1/equipment`
- `GET /api/v1/equipment/{equipment_id}`
- `PUT /api/v1/equipment/{equipment_id}`
- `DELETE /api/v1/equipment/{equipment_id}`

## Ingredient endpoints

- `POST /api/v1/ingredients`
- `GET /api/v1/ingredients`
- `GET /api/v1/ingredients/{ingredient_id}`
- `PUT /api/v1/ingredients/{ingredient_id}`
- `DELETE /api/v1/ingredients/{ingredient_id}`

## Style endpoints

- `GET /api/v1/styles/bjcp`
- `GET /api/v1/styles/bjcp/{style_identifier}`

Style lookup supports BJCP code (for example `21A`) or style name (for example `American IPA`) and returns water target ranges for brewing chemistry.

## Water Profile endpoints

- `POST /api/v1/water-profiles`
- `GET /api/v1/water-profiles`
- `GET /api/v1/water-profiles/{water_profile_id}`
- `PUT /api/v1/water-profiles/{water_profile_id}`
- `DELETE /api/v1/water-profiles/{water_profile_id}`
- `POST /api/v1/water-profiles/{water_profile_id}/recommendations`

Recommendation requests accept either `style_code` (BJCP) or `recipe_id` and return suggested mineral additions with projected ion profile.

## Inventory endpoints

- `POST /api/v1/inventory`
- `GET /api/v1/inventory`
- `GET /api/v1/inventory?low_stock_only=true`
- `GET /api/v1/inventory/alerts/low-stock`
- `GET /api/v1/inventory/{item_id}`
- `PUT /api/v1/inventory/{item_id}`
- `DELETE /api/v1/inventory/{item_id}`

## Analytics endpoint

- `GET /api/v1/analytics/overview`

## Fermentation endpoints

- `POST /api/v1/batches/{batch_id}/readings`
- `GET /api/v1/batches/{batch_id}/recipe-snapshot`
- `GET /api/v1/batches/{batch_id}/readings`
- `GET /api/v1/batches/{batch_id}/fermentation/trend`

`POST /api/v1/batches/{batch_id}/readings` accepts an optional `recorded_at` timestamp for backfilled readings.

`GET /api/v1/batches/{batch_id}/recipe-snapshot` returns the frozen recipe profile and ingredients captured when the batch was created.

## Batch Inventory Endpoints

- `GET /api/v1/batches/{batch_id}/inventory/preview`
- `POST /api/v1/batches/{batch_id}/inventory/consume`

The preview endpoint compares snapshot ingredient requirements against current inventory with unit conversion support (for example `g` <-> `kg`).

## External Import Endpoints

- `GET /api/v1/imports/recipes/catalog`
- `POST /api/v1/imports/recipes/import`
- `GET /api/v1/imports/equipment/catalog`
- `POST /api/v1/imports/equipment/import`
- `GET /api/v1/imports/equipment`
- `GET /api/v1/imports/equipment/{equipment_id}`
- `GET /api/v1/imports/ingredients/catalog`
- `POST /api/v1/imports/ingredients/import`

Current providers are adapter-backed template sources (`brewbench`, `craftdb`) so we can later switch to live external APIs without changing endpoint contracts. Recipe templates now include a Torpedo-style IPA clone example for substitution workflows.

## Timeline endpoints

- `POST /api/v1/batches/{batch_id}/timeline/steps`
- `GET /api/v1/batches/{batch_id}/timeline/steps`
- `PATCH /api/v1/batches/{batch_id}/timeline/steps/{step_id}`
- `GET /api/v1/notifications/upcoming-steps?window_minutes=120`

## Observability endpoint

- `GET /api/v1/observability/metrics`

Request middleware adds `X-Request-ID` response headers, structured request logs, and captures unhandled exceptions as `500` responses with `request_id` in body.

## Running tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Migration commands

```bash
cd backend
source .venv/bin/activate

# apply migrations
alembic upgrade head

# create a new migration after model changes
alembic revision -m "describe change"

# rollback one migration
alembic downgrade -1
```

## Next build steps

1. Add frontend (recommended: React Native or Blazor Hybrid).
2. Add brew analytics dashboards (efficiency trends, fermentation variance, repeatability).
3. Add device/sensor integrations for automated readings.
4. Add CI pipeline for lint/test/migration checks.
