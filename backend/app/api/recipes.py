from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.equipment_profile import EquipmentProfile
from app.models.recipe import Recipe, RecipeIngredient
from app.models.user import User
from app.schemas.recipe import RecipeCreate, RecipeRead, RecipeScaleRead, RecipeScaleRequest
from app.services.recipe_scaling import build_scaled_recipe

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _get_user_recipe_or_404(db: Session, recipe_id: int, user_id: int) -> Recipe:
    recipe = (
        db.query(Recipe)
        .filter(
            Recipe.id == recipe_id,
            Recipe.owner_user_id == user_id,
        )
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("", response_model=RecipeRead, status_code=201)
def create_recipe(
    payload: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Recipe:
    recipe = Recipe(
        owner_user_id=current_user.id,
        name=payload.name,
        style=payload.style,
        target_og=payload.target_og,
        target_fg=payload.target_fg,
        target_ibu=payload.target_ibu,
        target_srm=payload.target_srm,
        efficiency_pct=payload.efficiency_pct,
        notes=payload.notes,
    )

    for ingredient in payload.ingredients:
        recipe.ingredients.append(
            RecipeIngredient(
                name=ingredient.name,
                ingredient_type=ingredient.ingredient_type,
                amount=ingredient.amount,
                unit=ingredient.unit,
                stage=ingredient.stage,
                minute_added=ingredient.minute_added,
            )
        )

    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.get("", response_model=list[RecipeRead])
def list_recipes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Recipe]:
    return (
        db.query(Recipe)
        .filter(Recipe.owner_user_id == current_user.id)
        .order_by(Recipe.created_at.desc())
        .all()
    )


@router.get("/{recipe_id}", response_model=RecipeRead)
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Recipe:
    return _get_user_recipe_or_404(db, recipe_id=recipe_id, user_id=current_user.id)


@router.post("/{recipe_id}/scale", response_model=RecipeScaleRead)
def scale_recipe(
    recipe_id: int,
    payload: RecipeScaleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecipeScaleRead:
    recipe = _get_user_recipe_or_404(db, recipe_id=recipe_id, user_id=current_user.id)

    target_efficiency_pct = payload.target_efficiency_pct
    if payload.equipment_profile_id is not None:
        equipment = (
            db.query(EquipmentProfile)
            .filter(
                EquipmentProfile.id == payload.equipment_profile_id,
                EquipmentProfile.owner_user_id == current_user.id,
            )
            .first()
        )
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment profile not found")

        if target_efficiency_pct is None:
            target_efficiency_pct = equipment.brewhouse_efficiency_pct

    if target_efficiency_pct is None:
        target_efficiency_pct = recipe.efficiency_pct

    return build_scaled_recipe(
        recipe,
        source_batch_volume_liters=payload.source_batch_volume_liters,
        target_batch_volume_liters=payload.target_batch_volume_liters,
        target_efficiency_pct=target_efficiency_pct,
    )
