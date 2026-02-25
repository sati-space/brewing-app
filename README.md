# BrewPilot

AI-first homebrewing and beer brewing platform focused on smooth UX, practical automation, and better brew outcomes.

This repo currently contains:

- A detailed MVP plan.
- A Python FastAPI backend scaffold.
- SQL schema + seed data.
- Integration tests for key API flows.
- Alembic migrations and PostgreSQL local setup.

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

1. Add auth + user profiles.
2. Add brew day timeline API and notifications.
3. Connect an LLM provider for contextual guidance.
4. Add frontend (recommended: React Native or Blazor Hybrid).
