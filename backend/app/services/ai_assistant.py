from app.models.batch import Batch, FermentationReading
from app.models.recipe import Recipe
from app.schemas.ai import AISuggestion
from app.services.recipe_calculator import attenuation_pct, estimate_abv


class BrewAIAssistant:
    """Rules-based assistant; can later delegate to an LLM provider."""

    @staticmethod
    def optimize_recipe(recipe: Recipe, measured_og: float | None, measured_fg: float | None) -> list[AISuggestion]:
        suggestions: list[AISuggestion] = []

        og_to_compare = measured_og or recipe.target_og
        fg_to_compare = measured_fg or recipe.target_fg
        abv = estimate_abv(og_to_compare, fg_to_compare)
        attenuation = attenuation_pct(og_to_compare, fg_to_compare)

        if og_to_compare < recipe.target_og - 0.004:
            suggestions.append(
                AISuggestion(
                    title="Raise mash efficiency",
                    rationale="Measured/expected OG is below target, likely indicating extraction loss.",
                    action="Increase crush consistency, extend mash to 70 minutes, or reduce sparge rate.",
                    priority="high",
                )
            )

        if fg_to_compare > recipe.target_fg + 0.003:
            suggestions.append(
                AISuggestion(
                    title="Improve attenuation",
                    rationale="FG is trending higher than target and can leave the beer sweeter/heavier.",
                    action="Pitch a healthy starter, oxygenate wort, and review fermentation temperature ramp.",
                    priority="high",
                )
            )

        if recipe.target_ibu > 80:
            suggestions.append(
                AISuggestion(
                    title="Review bitterness balance",
                    rationale="Very high IBU can dominate perceived balance depending on style and FG.",
                    action="Shift part of bittering to later additions to keep perceived harshness lower.",
                    priority="medium",
                )
            )

        if abv > 8 and attenuation < 72:
            suggestions.append(
                AISuggestion(
                    title="High gravity fermentation risk",
                    rationale="High ABV with lower attenuation can stall early.",
                    action="Use nutrient additions and step fermentation temperature by 1 C after day 3.",
                    priority="medium",
                )
            )

        if not suggestions:
            suggestions.append(
                AISuggestion(
                    title="Recipe is aligned",
                    rationale="Current values sit close to your targets.",
                    action="Run this batch as planned and collect readings every 24 hours for model tuning.",
                    priority="low",
                )
            )

        return suggestions

    @staticmethod
    def diagnose_fermentation(batch: Batch, readings: list[FermentationReading]) -> list[AISuggestion]:
        suggestions: list[AISuggestion] = []

        if len(readings) < 2:
            return [
                AISuggestion(
                    title="More readings needed",
                    rationale="A single data point is not enough for reliable diagnosis.",
                    action="Add at least 2 more gravity and temperature readings over 48 hours.",
                    priority="medium",
                )
            ]

        sorted_readings = sorted(readings, key=lambda item: item.recorded_at)
        latest = sorted_readings[-1]
        prev = sorted_readings[-2]

        gravity_drop = 0.0
        if latest.gravity is not None and prev.gravity is not None:
            gravity_drop = prev.gravity - latest.gravity

        if gravity_drop < 0.001 and batch.status == "fermenting":
            suggestions.append(
                AISuggestion(
                    title="Potential stalled fermentation",
                    rationale="Gravity has barely moved since the previous reading.",
                    action="Check yeast viability, gently swirl fermenter, and verify temperature controller.",
                    priority="high",
                )
            )

        if latest.temp_c is not None and latest.temp_c > 24:
            suggestions.append(
                AISuggestion(
                    title="Fermentation temperature high",
                    rationale="Current fermentation temperature may produce unwanted esters/fusels.",
                    action="Lower temperature by 1-2 C and avoid sudden swings.",
                    priority="medium",
                )
            )

        if latest.ph is not None and latest.ph > 5.0:
            suggestions.append(
                AISuggestion(
                    title="pH trend check",
                    rationale="Fermentation pH appears higher than expected for active fermentation.",
                    action="Recalibrate meter and retest. If confirmed, inspect sanitation and yeast health.",
                    priority="medium",
                )
            )

        if not suggestions:
            suggestions.append(
                AISuggestion(
                    title="Fermentation on track",
                    rationale="Recent readings indicate healthy progression.",
                    action="Continue daily monitoring until gravity stabilizes for 2 consecutive days.",
                    priority="low",
                )
            )

        return suggestions
