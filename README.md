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

All recipe, batch, AI, inventory, timeline, and notifications endpoints require `Authorization: Bearer <token>`.

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

## Inventory endpoints

- `POST /api/v1/inventory`
- `GET /api/v1/inventory`
- `GET /api/v1/inventory?low_stock_only=true`
- `GET /api/v1/inventory/alerts/low-stock`
- `GET /api/v1/inventory/{item_id}`
- `PUT /api/v1/inventory/{item_id}`
- `DELETE /api/v1/inventory/{item_id}`

## Timeline endpoints

- `POST /api/v1/batches/{batch_id}/timeline/steps`
- `GET /api/v1/batches/{batch_id}/timeline/steps`
- `PATCH /api/v1/batches/{batch_id}/timeline/steps/{step_id}`
- `GET /api/v1/notifications/upcoming-steps?window_minutes=120`

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
2. Add observability (request logging, metrics, error tracking).
3. Add brew analytics dashboards (efficiency trends, fermentation variance, repeatability).
4. Add device/sensor integrations for automated readings.
