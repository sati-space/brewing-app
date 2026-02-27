import json
from datetime import datetime

from app.models.batch import Batch
from app.models.recipe import Recipe


def _ingredient_payload(recipe: Recipe) -> list[dict[str, object]]:
    ingredients = sorted(recipe.ingredients, key=lambda ingredient: ingredient.id)
    return [
        {
            "name": ingredient.name,
            "ingredient_type": ingredient.ingredient_type,
            "amount": ingredient.amount,
            "unit": ingredient.unit,
            "stage": ingredient.stage,
            "minute_added": ingredient.minute_added,
        }
        for ingredient in ingredients
    ]


def apply_recipe_snapshot(batch: Batch, recipe: Recipe) -> None:
    batch.recipe_snapshot_captured_at = datetime.utcnow()
    batch.recipe_name_snapshot = recipe.name
    batch.recipe_style_snapshot = recipe.style
    batch.recipe_target_og_snapshot = recipe.target_og
    batch.recipe_target_fg_snapshot = recipe.target_fg
    batch.recipe_target_ibu_snapshot = recipe.target_ibu
    batch.recipe_target_srm_snapshot = recipe.target_srm
    batch.recipe_efficiency_pct_snapshot = recipe.efficiency_pct
    batch.recipe_notes_snapshot = recipe.notes
    batch.recipe_ingredients_snapshot_json = json.dumps(_ingredient_payload(recipe))


def parse_snapshot_ingredients(batch: Batch) -> list[dict[str, object]]:
    raw_payload = batch.recipe_ingredients_snapshot_json
    if not raw_payload:
        return []

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    normalized: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "name": str(item.get("name", "")),
                "ingredient_type": str(item.get("ingredient_type", "")),
                "amount": float(item.get("amount", 0.0)),
                "unit": str(item.get("unit", "")),
                "stage": str(item.get("stage", "")),
                "minute_added": int(item.get("minute_added", 0)),
            }
        )
    return normalized
