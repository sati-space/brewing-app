from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.equipment_profile import EquipmentProfile
from app.models.inventory import InventoryItem
from app.models.recipe import Recipe, RecipeIngredient
from app.models.user import User
from app.schemas.recipe import (
    HopProfileRead,
    HopSubstitutionCandidateRead,
    RecipeCreate,
    RecipeHopSubstitutionRead,
    RecipeHopSubstitutionRequest,
    RecipeRead,
    RecipeScaleRead,
    RecipeScaleRequest,
)
from app.services.hop_substitution import normalize_hop_name, recommend_hop_substitutions, resolve_hop_profile
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


@router.post("/{recipe_id}/hop-substitutions", response_model=RecipeHopSubstitutionRead)
def recommend_recipe_hop_substitutions(
    recipe_id: int,
    payload: RecipeHopSubstitutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecipeHopSubstitutionRead:
    recipe = _get_user_recipe_or_404(db, recipe_id=recipe_id, user_id=current_user.id)

    recipe_hop_names = [
        ingredient.name
        for ingredient in recipe.ingredients
        if ingredient.ingredient_type.strip().lower() == "hop"
    ]
    if not recipe_hop_names:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recipe has no hop ingredients to substitute.",
        )

    normalized_target = normalize_hop_name(payload.target_hop_name)
    target_profile = resolve_hop_profile(payload.target_hop_name)
    recipe_hop_profiles = {profile.name for profile in (resolve_hop_profile(name) for name in recipe_hop_names) if profile}
    target_in_recipe = normalized_target in {normalize_hop_name(name) for name in recipe_hop_names}
    if target_profile and target_profile.name in recipe_hop_profiles:
        target_in_recipe = True

    if not target_in_recipe:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Target hop is not present in this recipe.",
        )

    candidate_names = [name for name in payload.available_hop_names if name.strip()]
    source_parts: list[str] = []
    if candidate_names:
        source_parts.append("provided")

    if payload.include_inventory_hops:
        inventory_hop_names = [
            item.name
            for item in (
                db.query(InventoryItem)
                .filter(
                    InventoryItem.owner_user_id == current_user.id,
                    func.lower(InventoryItem.ingredient_type) == "hop",
                )
                .all()
            )
        ]
        if inventory_hop_names:
            source_parts.append("inventory")
            candidate_names.extend(inventory_hop_names)

    if not candidate_names:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No candidate hops found. Provide available_hop_names or add hop inventory.",
        )

    try:
        result = recommend_hop_substitutions(
            target_hop_name=payload.target_hop_name,
            available_hop_names=candidate_names,
            top_k=payload.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return RecipeHopSubstitutionRead(
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        target_hop_name=payload.target_hop_name,
        target_hop_profile=HopProfileRead(
            name=result.target_hop.name,
            alpha_acid_min_pct=result.target_hop.alpha_acid_min_pct,
            alpha_acid_max_pct=result.target_hop.alpha_acid_max_pct,
            flavor_descriptors=list(result.target_hop.flavor_descriptors),
        ),
        candidate_source="+".join(source_parts) if source_parts else "provided",
        candidate_input_count=len(candidate_names),
        recognized_candidate_count=result.recognized_candidate_count,
        unresolved_hop_names=list(result.unresolved_hop_names),
        substitutions=[
            HopSubstitutionCandidateRead(
                name=row.name,
                alpha_acid_min_pct=row.alpha_acid_min_pct,
                alpha_acid_max_pct=row.alpha_acid_max_pct,
                flavor_similarity_score=row.flavor_similarity_score,
                descriptor_overlap_score=row.descriptor_overlap_score,
                similarity_score=row.similarity_score,
                recommended_bittering_ratio=row.recommended_bittering_ratio,
                shared_descriptors=list(row.shared_descriptors),
            )
            for row in result.substitutions
        ],
    )
