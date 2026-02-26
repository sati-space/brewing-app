from datetime import date, datetime

import pytest

from app.core.config import settings
from app.models.batch import Batch, FermentationReading
from app.models.recipe import Recipe
from app.schemas.ai import AISuggestion
from app.services import ai_orchestrator


@pytest.fixture
def recipe() -> Recipe:
    return Recipe(
        id=1,
        owner_user_id=1,
        name="Test IPA",
        style="21A",
        target_og=1.060,
        target_fg=1.012,
        target_ibu=60,
        target_srm=8,
        efficiency_pct=72,
        notes="",
    )


@pytest.fixture
def batch() -> Batch:
    return Batch(
        id=1,
        owner_user_id=1,
        recipe_id=1,
        name="Batch 1",
        brewed_on=date(2026, 2, 26),
        status="fermenting",
        volume_liters=20.0,
        measured_og=1.060,
        measured_fg=None,
        notes="",
    )


@pytest.fixture
def readings() -> list[FermentationReading]:
    return [
        FermentationReading(id=1, batch_id=1, recorded_at=datetime(2026, 2, 25, 12, 0), gravity=1.030, temp_c=20.0, ph=4.5),
        FermentationReading(id=2, batch_id=1, recorded_at=datetime(2026, 2, 26, 12, 0), gravity=1.0295, temp_c=20.5, ph=4.6),
    ]


def test_optimize_recipe_rules_source_when_llm_disabled(recipe: Recipe, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "rules")

    suggestions, source = ai_orchestrator.optimize_recipe(recipe=recipe, measured_og=1.050, measured_fg=1.016)

    assert source == "rules"
    assert suggestions


def test_optimize_recipe_uses_llm_when_enabled(recipe: Recipe, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "llm")
    monkeypatch.setattr(settings, "ai_llm_base_url", "https://example.com")
    monkeypatch.setattr(settings, "ai_llm_model", "test-model")

    class FakeClient:
        def __init__(self, **_: object):
            pass

        def suggest(self, *, system_prompt: str, user_prompt: str) -> list[AISuggestion]:
            assert system_prompt
            assert user_prompt
            return [
                AISuggestion(
                    title="LLM tip",
                    rationale="Context-aware recommendation",
                    action="Do something practical",
                    priority="medium",
                )
            ]

    monkeypatch.setattr(ai_orchestrator, "OpenAICompatibleLLM", FakeClient)

    suggestions, source = ai_orchestrator.optimize_recipe(recipe=recipe, measured_og=1.050, measured_fg=1.016)

    assert source == "llm"
    assert suggestions[0].title == "LLM tip"


def test_optimize_recipe_falls_back_when_llm_fails(recipe: Recipe, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "llm")
    monkeypatch.setattr(settings, "ai_llm_base_url", "https://example.com")
    monkeypatch.setattr(settings, "ai_llm_model", "test-model")

    class ExplodingClient:
        def __init__(self, **_: object):
            pass

        def suggest(self, *, system_prompt: str, user_prompt: str) -> list[AISuggestion]:
            raise ai_orchestrator.LLMProviderError("boom")

    monkeypatch.setattr(ai_orchestrator, "OpenAICompatibleLLM", ExplodingClient)

    suggestions, source = ai_orchestrator.optimize_recipe(recipe=recipe, measured_og=1.050, measured_fg=1.016)

    assert source == "llm_fallback"
    assert suggestions


def test_diagnose_fermentation_uses_rules_or_fallback(
    batch: Batch,
    readings: list[FermentationReading],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_provider", "llm")
    monkeypatch.setattr(settings, "ai_llm_base_url", "")
    monkeypatch.setattr(settings, "ai_llm_model", "")

    suggestions, source = ai_orchestrator.diagnose_fermentation(batch=batch, readings=readings)

    assert source == "llm_fallback"
    assert suggestions
