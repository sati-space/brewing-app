# BrewPilot MVP Spec

## Product vision

Build a modern, AI-assisted brewing platform that helps homebrewers design better recipes, execute cleaner brew days, and continuously improve from fermentation and tasting outcomes.

## Core user personas

1. **Homebrewer (beginner/intermediate)**: needs guidance and guardrails.
2. **Power brewer (advanced)**: wants precision, data logging, and optimization.
3. **Small craft pilot brewer**: wants repeatability, process control, and team visibility.

## MVP goals (first release)

1. Replace spreadsheet/manual workflows for recipe and batch tracking.
2. Offer practical AI support (not generic chat).
3. Deliver a smooth, mobile-first workflow for brew day and fermentation.

## Non-goals for MVP

1. Full marketplace/e-commerce.
2. Lab-grade QA integrations.
3. Deep IoT hardware control (read-only integrations can come earlier).

## MVP feature scope

### 1) Recipe Builder

- Create and edit recipes with ingredients, steps, and target profile.
- Auto-calculate OG, FG estimate, ABV estimate, IBU, SRM.
- Style tagging (BJCP style code field).

### 2) Batch Tracking

- Create a batch from a recipe snapshot.
- Log actual brew metrics (mash temp, OG, volume, notes).
- Track status: planned -> brewing -> fermenting -> conditioning -> packaged.

### 3) Fermentation Log

- Time-series readings: gravity, temperature, pH.
- Lightweight trend view data API.
- Alert flags (example: gravity plateau risk).

### 4) Inventory

- Track ingredient quantities and thresholds.
- Show low-stock warnings.
- Basic substitution recommendations in AI responses.

### 5) AI Assistant (MVP)

- Endpoint to analyze a recipe and suggest:
  - efficiency adjustments,
  - ABV/attenuation corrections,
  - bittering balance adjustments,
  - ingredient substitution ideas.
- Endpoint to analyze fermentation readings and surface likely issues and next checks.

## AI design principles

1. Ground responses in user data (recipes, readings, inventory).
2. Provide explainable suggestions with reason + impact.
3. Be conservative and safety-aware (especially contamination or pressure scenarios).
4. Keep final control with brewer (never auto-edit recipe silently).

## Data model (MVP)

### Primary entities

- `users` (future auth-ready)
- `recipes`
- `recipe_ingredients`
- `batches`
- `fermentation_readings`
- `inventory_items`

### Key relationships

- A recipe has many recipe ingredients.
- A batch references a recipe snapshot.
- A batch has many fermentation readings.
- Inventory items map to ingredient names/types.

## API surface (MVP)

- `GET /api/v1/health`
- `POST /api/v1/recipes`
- `GET /api/v1/recipes`
- `GET /api/v1/recipes/{recipe_id}`
- `POST /api/v1/batches`
- `GET /api/v1/batches`
- `POST /api/v1/batches/{batch_id}/readings`
- `POST /api/v1/ai/recipe-optimize`
- `POST /api/v1/ai/fermentation-diagnose`

## Suggested architecture

### Backend

- Python + FastAPI
- SQLAlchemy ORM + Alembic migrations
- PostgreSQL (SQLite for local dev)
- Background jobs (future): Celery/RQ or lightweight task queue

### Frontend options

1. React Native (fast mobile-first UX)
2. Blazor Hybrid / .NET MAUI (fits C# strength)

### AI layer

- Service abstraction with pluggable providers:
  - Rules engine (always available, deterministic)
  - LLM provider (OpenAI/other) when configured

## Delivery plan

### Phase 1 (Week 1-2)

- Backend foundations, schema, recipe + batch CRUD.

### Phase 2 (Week 3-4)

- Fermentation readings + AI endpoints (rules-first).

### Phase 3 (Week 5-6)

- Frontend MVP and brew day workflows.

### Phase 4 (Week 7-8)

- Polishing, analytics, onboarding, and beta testing.

## Success metrics

1. Recipe-to-batch conversion rate.
2. Number of logged fermentation readings per batch.
3. AI suggestion acceptance rate.
4. Repeat batch improvements (variance reduction in OG/FG outcomes).

## Collaboration setup for us

1. You (Python/C#/SQL) can own API features, SQL tuning, and integration logic.
2. I can accelerate architecture, code generation, refactors, and test scaffolding.
3. We iterate in short cycles: define feature -> implement endpoint -> test -> ship.
