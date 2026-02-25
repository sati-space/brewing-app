from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.recipe import Recipe, RecipeIngredient
from app.models.user import User
from app.schemas.recipe import RecipeCreate, RecipeRead

router = APIRouter(prefix="/recipes", tags=["recipes"])


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
    recipe = (
        db.query(Recipe)
        .filter(
            Recipe.id == recipe_id,
            Recipe.owner_user_id == current_user.id,
        )
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe
