from app.core.config import settings
from app.models.batch import Batch, FermentationReading
from app.models.recipe import Recipe
from app.schemas.ai import AISuggestion
from app.services.ai_assistant import BrewAIAssistant
from app.services.llm_provider import LLMProviderError, OpenAICompatibleLLM


def _llm_enabled() -> bool:
    return settings.ai_provider.lower() == "llm"


def _build_llm_client() -> OpenAICompatibleLLM:
    if not settings.ai_llm_base_url or not settings.ai_llm_model:
        raise LLMProviderError("LLM provider is enabled but AI_LLM_BASE_URL or AI_LLM_MODEL is missing")

    return OpenAICompatibleLLM(
        base_url=settings.ai_llm_base_url,
        api_key=settings.ai_llm_api_key,
        model=settings.ai_llm_model,
        timeout_seconds=settings.ai_llm_timeout_seconds,
    )


def _recipe_prompts(recipe: Recipe, measured_og: float | None, measured_fg: float | None) -> tuple[str, str]:
    system_prompt = (
        "You are a brewing assistant. Output JSON only with shape: "
        '{"suggestions":[{"title":"...","rationale":"...","action":"...","priority":"low|medium|high"}]}. '
        "Keep suggestions practical, concise, and safety-aware."
    )

    user_prompt = (
        f"Recipe: {recipe.name}\n"
        f"Style: {recipe.style}\n"
        f"Target OG: {recipe.target_og}\n"
        f"Target FG: {recipe.target_fg}\n"
        f"Target IBU: {recipe.target_ibu}\n"
        f"Target SRM: {recipe.target_srm}\n"
        f"Efficiency %: {recipe.efficiency_pct}\n"
        f"Measured OG: {measured_og}\n"
        f"Measured FG: {measured_fg}\n"
        f"Ingredients: {[i.name for i in recipe.ingredients]}\n"
        "Return 1-4 actionable suggestions."
    )

    return system_prompt, user_prompt


def _fermentation_prompts(batch: Batch, readings: list[FermentationReading]) -> tuple[str, str]:
    system_prompt = (
        "You are a brewing assistant diagnosing fermentation. Output JSON only with shape: "
        '{"suggestions":[{"title":"...","rationale":"...","action":"...","priority":"low|medium|high"}]}. '
        "Keep suggestions practical, conservative, and safety-aware."
    )

    serialized_readings = [
        {
            "recorded_at": r.recorded_at.isoformat(),
            "gravity": r.gravity,
            "temp_c": r.temp_c,
            "ph": r.ph,
        }
        for r in sorted(readings, key=lambda item: item.recorded_at)
    ]

    user_prompt = (
        f"Batch: {batch.name}\n"
        f"Status: {batch.status}\n"
        f"Volume liters: {batch.volume_liters}\n"
        f"Measured OG: {batch.measured_og}\n"
        f"Measured FG: {batch.measured_fg}\n"
        f"Readings: {serialized_readings}\n"
        "Return 1-4 actionable suggestions."
    )

    return system_prompt, user_prompt


def optimize_recipe(recipe: Recipe, measured_og: float | None, measured_fg: float | None) -> tuple[list[AISuggestion], str]:
    rules_suggestions = BrewAIAssistant.optimize_recipe(
        recipe=recipe,
        measured_og=measured_og,
        measured_fg=measured_fg,
    )

    if not _llm_enabled():
        return rules_suggestions, "rules"

    try:
        client = _build_llm_client()
        system_prompt, user_prompt = _recipe_prompts(recipe=recipe, measured_og=measured_og, measured_fg=measured_fg)
        llm_suggestions = client.suggest(system_prompt=system_prompt, user_prompt=user_prompt)
        return llm_suggestions, "llm"
    except LLMProviderError:
        return rules_suggestions, "llm_fallback"


def diagnose_fermentation(batch: Batch, readings: list[FermentationReading]) -> tuple[list[AISuggestion], str]:
    rules_suggestions = BrewAIAssistant.diagnose_fermentation(batch=batch, readings=readings)

    if not _llm_enabled():
        return rules_suggestions, "rules"

    try:
        client = _build_llm_client()
        system_prompt, user_prompt = _fermentation_prompts(batch=batch, readings=readings)
        llm_suggestions = client.suggest(system_prompt=system_prompt, user_prompt=user_prompt)
        return llm_suggestions, "llm"
    except LLMProviderError:
        return rules_suggestions, "llm_fallback"
