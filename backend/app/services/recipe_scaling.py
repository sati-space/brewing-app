from app.models.recipe import Recipe
from app.schemas.recipe import RecipeScaleRead, ScaledRecipeIngredientRead
from app.services.recipe_calculator import estimate_abv


def _round(value: float, decimals: int = 3) -> float:
    return round(value, decimals)


def build_scaled_recipe(
    recipe: Recipe,
    *,
    source_batch_volume_liters: float,
    target_batch_volume_liters: float,
    target_efficiency_pct: float,
) -> RecipeScaleRead:
    scale_factor = target_batch_volume_liters / source_batch_volume_liters

    source_efficiency_pct = recipe.efficiency_pct
    efficiency_ratio = target_efficiency_pct / source_efficiency_pct if source_efficiency_pct > 0 else 1.0

    og_points = max((recipe.target_og - 1.0) * 1000.0, 0.0)
    scaled_og_points = og_points * efficiency_ratio
    estimated_target_og = 1.0 + (scaled_og_points / 1000.0)

    source_points = max((recipe.target_og - 1.0) * 1000.0, 0.0001)
    attenuation = max(min((recipe.target_og - recipe.target_fg) * 1000.0 / source_points, 1.0), 0.0)
    estimated_target_fg = estimated_target_og - attenuation * (estimated_target_og - 1.0)

    ingredients = [
        ScaledRecipeIngredientRead(
            name=ingredient.name,
            ingredient_type=ingredient.ingredient_type,
            original_amount=_round(ingredient.amount, 4),
            scaled_amount=_round(ingredient.amount * scale_factor, 4),
            unit=ingredient.unit,
            stage=ingredient.stage,
            minute_added=ingredient.minute_added,
        )
        for ingredient in sorted(recipe.ingredients, key=lambda item: item.id)
    ]

    return RecipeScaleRead(
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        style=recipe.style,
        source_batch_volume_liters=_round(source_batch_volume_liters, 4),
        target_batch_volume_liters=_round(target_batch_volume_liters, 4),
        scale_factor=_round(scale_factor, 4),
        source_efficiency_pct=_round(source_efficiency_pct, 2),
        target_efficiency_pct=_round(target_efficiency_pct, 2),
        estimated_target_og=_round(estimated_target_og, 3),
        estimated_target_fg=_round(estimated_target_fg, 3),
        estimated_abv=estimate_abv(_round(estimated_target_og, 3), _round(estimated_target_fg, 3)),
        target_ibu=_round(recipe.target_ibu, 2),
        target_srm=_round(recipe.target_srm, 2),
        ingredients=ingredients,
    )
