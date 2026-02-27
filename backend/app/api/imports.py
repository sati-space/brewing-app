from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.equipment_profile import EquipmentProfile
from app.models.recipe import Recipe, RecipeIngredient
from app.models.user import User
from app.schemas.imports import (
    EquipmentImportResultRead,
    EquipmentProfileRead,
    ExternalEquipmentCatalogItemRead,
    ExternalEquipmentCatalogResponse,
    ExternalImportRequest,
    ExternalRecipeCatalogIngredientRead,
    ExternalRecipeCatalogItemRead,
    ExternalRecipeCatalogResponse,
    RecipeImportResultRead,
)
from app.services.external_catalog import (
    ExternalEquipmentTemplate,
    ExternalRecipeTemplate,
    get_equipment_template,
    get_recipe_template,
    list_equipment_templates,
    list_recipe_templates,
)

router = APIRouter(prefix="/imports", tags=["imports"])


def _to_recipe_catalog_item(template: ExternalRecipeTemplate) -> ExternalRecipeCatalogItemRead:
    ingredients = [
        ExternalRecipeCatalogIngredientRead(
            name=ingredient.name,
            ingredient_type=ingredient.ingredient_type,
            amount=ingredient.amount,
            unit=ingredient.unit,
            stage=ingredient.stage,
            minute_added=ingredient.minute_added,
        )
        for ingredient in template.ingredients
    ]

    return ExternalRecipeCatalogItemRead(
        provider=template.provider,
        external_id=template.external_id,
        name=template.name,
        style=template.style,
        target_og=template.target_og,
        target_fg=template.target_fg,
        target_ibu=template.target_ibu,
        target_srm=template.target_srm,
        efficiency_pct=template.efficiency_pct,
        notes=template.notes,
        ingredients=ingredients,
    )


def _to_equipment_catalog_item(template: ExternalEquipmentTemplate) -> ExternalEquipmentCatalogItemRead:
    return ExternalEquipmentCatalogItemRead(
        provider=template.provider,
        external_id=template.external_id,
        name=template.name,
        batch_volume_liters=template.batch_volume_liters,
        mash_tun_volume_liters=template.mash_tun_volume_liters,
        boil_kettle_volume_liters=template.boil_kettle_volume_liters,
        brewhouse_efficiency_pct=template.brewhouse_efficiency_pct,
        boil_off_rate_l_per_hour=template.boil_off_rate_l_per_hour,
        trub_loss_liters=template.trub_loss_liters,
        notes=template.notes,
    )


@router.get("/recipes/catalog", response_model=ExternalRecipeCatalogResponse)
def list_recipe_catalog(
    provider: str | None = Query(default=None),
    search: str | None = Query(default=None),
    _: User = Depends(get_current_user),
) -> ExternalRecipeCatalogResponse:
    templates = list_recipe_templates(provider=provider, search=search)
    items = [_to_recipe_catalog_item(template) for template in templates]
    return ExternalRecipeCatalogResponse(count=len(items), items=items)


@router.post("/recipes/import", response_model=RecipeImportResultRead, status_code=status.HTTP_201_CREATED)
def import_recipe_from_catalog(
    payload: ExternalImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecipeImportResultRead:
    template = get_recipe_template(provider=payload.provider, external_id=payload.external_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="External recipe not found")

    recipe = Recipe(
        owner_user_id=current_user.id,
        name=template.name,
        style=template.style,
        target_og=template.target_og,
        target_fg=template.target_fg,
        target_ibu=template.target_ibu,
        target_srm=template.target_srm,
        efficiency_pct=template.efficiency_pct,
        notes=template.notes,
    )

    for ingredient in template.ingredients:
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

    return RecipeImportResultRead(
        provider=template.provider,
        external_id=template.external_id,
        recipe_id=recipe.id,
        recipe_name=recipe.name,
    )


@router.get("/equipment/catalog", response_model=ExternalEquipmentCatalogResponse)
def list_equipment_catalog(
    provider: str | None = Query(default=None),
    search: str | None = Query(default=None),
    _: User = Depends(get_current_user),
) -> ExternalEquipmentCatalogResponse:
    templates = list_equipment_templates(provider=provider, search=search)
    items = [_to_equipment_catalog_item(template) for template in templates]
    return ExternalEquipmentCatalogResponse(count=len(items), items=items)


@router.post("/equipment/import", response_model=EquipmentImportResultRead, status_code=status.HTTP_201_CREATED)
def import_equipment_profile(
    payload: ExternalImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EquipmentImportResultRead:
    template = get_equipment_template(provider=payload.provider, external_id=payload.external_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="External equipment profile not found")

    existing = (
        db.query(EquipmentProfile)
        .filter(
            EquipmentProfile.owner_user_id == current_user.id,
            EquipmentProfile.source_provider == template.provider,
            EquipmentProfile.source_external_id == template.external_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Equipment profile already imported")

    equipment_profile = EquipmentProfile(
        owner_user_id=current_user.id,
        source_provider=template.provider,
        source_external_id=template.external_id,
        name=template.name,
        batch_volume_liters=template.batch_volume_liters,
        mash_tun_volume_liters=template.mash_tun_volume_liters,
        boil_kettle_volume_liters=template.boil_kettle_volume_liters,
        brewhouse_efficiency_pct=template.brewhouse_efficiency_pct,
        boil_off_rate_l_per_hour=template.boil_off_rate_l_per_hour,
        trub_loss_liters=template.trub_loss_liters,
        notes=template.notes,
    )

    db.add(equipment_profile)
    db.commit()
    db.refresh(equipment_profile)

    return EquipmentImportResultRead(
        provider=template.provider,
        external_id=template.external_id,
        equipment_profile=EquipmentProfileRead.model_validate(equipment_profile),
    )


@router.get("/equipment", response_model=list[EquipmentProfileRead])
def list_imported_equipment_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EquipmentProfile]:
    return (
        db.query(EquipmentProfile)
        .filter(EquipmentProfile.owner_user_id == current_user.id)
        .order_by(EquipmentProfile.created_at.desc(), EquipmentProfile.id.desc())
        .all()
    )


@router.get("/equipment/{equipment_id}", response_model=EquipmentProfileRead)
def get_imported_equipment_profile(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EquipmentProfile:
    equipment_profile = (
        db.query(EquipmentProfile)
        .filter(
            EquipmentProfile.id == equipment_id,
            EquipmentProfile.owner_user_id == current_user.id,
        )
        .first()
    )
    if not equipment_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment profile not found")

    return equipment_profile
