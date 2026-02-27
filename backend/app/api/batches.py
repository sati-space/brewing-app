from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.batch import Batch, FermentationReading
from app.models.brew_step import BrewStep
from app.models.equipment_profile import EquipmentProfile
from app.models.inventory import InventoryItem
from app.models.recipe import Recipe
from app.models.user import User
from app.models.water_profile import WaterProfile
from app.schemas.batch import (
    BatchCreate,
    BrewPlanAppliedStepRead,
    BrewPlanApplyTimelineRead,
    BrewPlanApplyTimelineRequest,
    BatchInventoryConsumeRead,
    BatchInventoryPreviewRead,
    BrewPlanMineralAdditionRead,
    BrewPlanRead,
    BrewPlanRequest,
    BrewPlanWaterIonRead,
    BrewPlanWaterRead,
    BatchRead,
    BatchRecipeSnapshotRead,
    FermentationReadingCreate,
    FermentationReadingRead,
    FermentationTrendRead,
    RecipeIngredientSnapshotRead,
)
from app.services.batch_snapshot import apply_recipe_snapshot, parse_snapshot_ingredients
from app.services.bjcp_styles import resolve_bjcp_style
from app.services.brew_plan import build_brew_day_plan
from app.services.fermentation import build_fermentation_trend
from app.services.inventory_consumption import build_inventory_preview, consume_inventory_for_batch
from app.services.water_recommendation import build_water_recommendation

router = APIRouter(prefix="/batches", tags=["batches"])


def _get_user_batch_or_404(db: Session, batch_id: int, user_id: int) -> Batch:
    batch = (
        db.query(Batch)
        .filter(
            Batch.id == batch_id,
            Batch.owner_user_id == user_id,
        )
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


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


def _compose_brew_plan(
    *,
    db: Session,
    batch: Batch,
    recipe: Recipe,
    current_user: User,
    payload: BrewPlanRequest,
) -> BrewPlanRead:
    equipment: EquipmentProfile | None = None
    if payload.equipment_profile_id is not None:
        equipment = (
            db.query(EquipmentProfile)
            .filter(
                EquipmentProfile.id == payload.equipment_profile_id,
                EquipmentProfile.owner_user_id == current_user.id,
            )
            .first()
        )
        if equipment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment profile not found")

    inventory_preview = build_inventory_preview(db, batch=batch, user_id=current_user.id)
    snapshot_ingredients = parse_snapshot_ingredients(batch)
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

    core_plan = build_brew_day_plan(
        batch=batch,
        inventory_preview=inventory_preview,
        equipment=equipment,
        snapshot_ingredients=snapshot_ingredients,
        inventory_hop_names=inventory_hop_names,
        extra_available_hops=payload.available_hop_names,
        brew_start_at=payload.brew_start_at,
    )

    style_identifier = payload.style_code or batch.recipe_style_snapshot or recipe.style
    water_recommendation: BrewPlanWaterRead | None = None
    notes = list(core_plan.notes)
    if payload.water_profile_id is not None:
        water_profile = (
            db.query(WaterProfile)
            .filter(
                WaterProfile.id == payload.water_profile_id,
                WaterProfile.owner_user_id == current_user.id,
            )
            .first()
        )
        if water_profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Water profile not found")

        style = resolve_bjcp_style(style_identifier)
        if style is None:
            notes.append("Water recommendation skipped because the batch style is not mapped to BJCP data.")
        else:
            water_plan = build_water_recommendation(
                water_profile=water_profile,
                style=style,
                batch_volume_liters=batch.volume_liters,
            )
            water_recommendation = BrewPlanWaterRead(
                water_profile_id=water_profile.id,
                water_profile_name=water_profile.name,
                style_code=style.code,
                style_name=style.name,
                source_profile=BrewPlanWaterIonRead(**water_plan.source_profile.__dict__),
                target_profile=BrewPlanWaterIonRead(**water_plan.target_profile.__dict__),
                projected_profile=BrewPlanWaterIonRead(**water_plan.projected_profile.__dict__),
                additions=[BrewPlanMineralAdditionRead(**row.__dict__) for row in water_plan.additions],
                notes=list(water_plan.notes),
            )
    else:
        notes.append("No water profile selected; water chemistry recommendation not included.")

    return BrewPlanRead(
        batch_id=batch.id,
        batch_name=batch.name,
        style=style_identifier,
        generated_at=datetime.utcnow(),
        volumes=core_plan.volumes,
        gravity=core_plan.gravity,
        equipment=core_plan.equipment,
        inventory_shortage_count=inventory_preview.shortage_count,
        shopping_list=core_plan.shopping_list,
        hop_substitutions=core_plan.hop_substitutions,
        water_recommendation=water_recommendation,
        timer_plan=core_plan.timer_plan,
        notes=notes,
    )


@router.post("", response_model=BatchRead, status_code=201)
def create_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Batch:
    recipe = _get_user_recipe_or_404(db, recipe_id=payload.recipe_id, user_id=current_user.id)

    batch = Batch(
        owner_user_id=current_user.id,
        recipe_id=payload.recipe_id,
        name=payload.name,
        brewed_on=payload.brewed_on,
        status=payload.status,
        volume_liters=payload.volume_liters,
        measured_og=payload.measured_og,
        measured_fg=payload.measured_fg,
        notes=payload.notes,
    )
    apply_recipe_snapshot(batch, recipe)

    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("", response_model=list[BatchRead])
def list_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Batch]:
    return (
        db.query(Batch)
        .filter(Batch.owner_user_id == current_user.id)
        .order_by(Batch.created_at.desc())
        .all()
    )


@router.get("/{batch_id}/recipe-snapshot", response_model=BatchRecipeSnapshotRead)
def get_batch_recipe_snapshot(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchRecipeSnapshotRead:
    batch = _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)

    ingredient_payload = parse_snapshot_ingredients(batch)
    ingredients = [
        RecipeIngredientSnapshotRead(**item)
        for item in ingredient_payload
    ]

    return BatchRecipeSnapshotRead(
        batch_id=batch.id,
        recipe_id=batch.recipe_id,
        captured_at=batch.recipe_snapshot_captured_at or batch.created_at,
        name=batch.recipe_name_snapshot,
        style=batch.recipe_style_snapshot,
        target_og=batch.recipe_target_og_snapshot,
        target_fg=batch.recipe_target_fg_snapshot,
        target_ibu=batch.recipe_target_ibu_snapshot,
        target_srm=batch.recipe_target_srm_snapshot,
        efficiency_pct=batch.recipe_efficiency_pct_snapshot,
        notes=batch.recipe_notes_snapshot,
        ingredients=ingredients,
    )


@router.get("/{batch_id}/inventory/preview", response_model=BatchInventoryPreviewRead)
def get_batch_inventory_preview(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchInventoryPreviewRead:
    batch = _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)
    return build_inventory_preview(db, batch=batch, user_id=current_user.id)


@router.post("/{batch_id}/inventory/consume", response_model=BatchInventoryConsumeRead)
def consume_batch_inventory(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchInventoryConsumeRead:
    batch = _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)
    result = consume_inventory_for_batch(db, batch=batch, user_id=current_user.id)

    if not result.consumed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result.model_dump(mode="json"))

    return result


@router.post("/{batch_id}/brew-plan", response_model=BrewPlanRead)
def generate_brew_plan(
    batch_id: int,
    payload: BrewPlanRequest = Body(default_factory=BrewPlanRequest),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrewPlanRead:
    batch = _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)
    recipe = _get_user_recipe_or_404(db, recipe_id=batch.recipe_id, user_id=current_user.id)
    return _compose_brew_plan(
        db=db,
        batch=batch,
        recipe=recipe,
        current_user=current_user,
        payload=payload,
    )


@router.post("/{batch_id}/brew-plan/apply-timeline", response_model=BrewPlanApplyTimelineRead)
def apply_brew_plan_to_timeline(
    batch_id: int,
    payload: BrewPlanApplyTimelineRequest = Body(default_factory=BrewPlanApplyTimelineRequest),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BrewPlanApplyTimelineRead:
    batch = _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)
    recipe = _get_user_recipe_or_404(db, recipe_id=batch.recipe_id, user_id=current_user.id)
    brew_plan = _compose_brew_plan(
        db=db,
        batch=batch,
        recipe=recipe,
        current_user=current_user,
        payload=payload,
    )

    existing_steps = (
        db.query(BrewStep)
        .filter(
            BrewStep.batch_id == batch.id,
            BrewStep.owner_user_id == current_user.id,
        )
        .order_by(BrewStep.step_order.asc(), BrewStep.created_at.asc())
        .all()
    )

    to_delete: list[BrewStep] = []
    preserved_steps: list[BrewStep] = existing_steps
    if payload.replace_existing_pending_steps:
        to_delete = [step for step in existing_steps if step.status in {"pending", "skipped"}]
        preserved_steps = [step for step in existing_steps if step not in to_delete]
        for step in to_delete:
            db.delete(step)

    next_order = max((step.step_order for step in preserved_steps), default=0) + 1
    created_steps: list[tuple[BrewStep, str]] = []

    prep_steps: list[tuple[str, str, str, datetime | None, int | None, float | None]] = []
    if payload.include_shopping_step and brew_plan.shopping_list:
        shopping_names = ", ".join(item.name for item in brew_plan.shopping_list[:5])
        description = f"Missing ingredients: {shopping_names}."
        prep_scheduled = payload.brew_start_at - timedelta(minutes=45) if payload.brew_start_at else None
        prep_steps.append(("shopping", "Resolve ingredient gaps", description, prep_scheduled, 20, None))

    if payload.include_water_step and brew_plan.water_recommendation and brew_plan.water_recommendation.additions:
        addition_names = ", ".join(item.mineral_name for item in brew_plan.water_recommendation.additions[:4])
        description = f"Prepare additions: {addition_names}."
        water_scheduled = payload.brew_start_at - timedelta(minutes=20) if payload.brew_start_at else None
        prep_steps.append(("water_adjust", "Prepare water additions", description, water_scheduled, 15, None))

    for timer_key, name, description, scheduled_for, duration_minutes, target_temp_c in prep_steps:
        step = BrewStep(
            batch_id=batch.id,
            owner_user_id=current_user.id,
            step_order=next_order,
            name=name,
            description=f"[{timer_key}] {description}",
            scheduled_for=scheduled_for,
            duration_minutes=duration_minutes,
            target_temp_c=target_temp_c,
            status="pending",
            completed_at=None,
        )
        db.add(step)
        db.flush()
        created_steps.append((step, timer_key))
        next_order += 1

    for timer_step in brew_plan.timer_plan:
        step = BrewStep(
            batch_id=batch.id,
            owner_user_id=current_user.id,
            step_order=next_order,
            name=timer_step.name,
            description=f"[{timer_step.timer_key}] Auto-generated from brew plan.",
            scheduled_for=timer_step.planned_start_at,
            duration_minutes=timer_step.duration_minutes,
            target_temp_c=timer_step.target_temp_c,
            status="pending",
            completed_at=None,
        )
        db.add(step)
        db.flush()
        created_steps.append((step, timer_step.timer_key))
        next_order += 1

    db.commit()

    applied_steps = [
        BrewPlanAppliedStepRead(
            step_id=step.id,
            step_order=step.step_order,
            timer_key=timer_key,
            name=step.name,
            status=step.status,
            scheduled_for=step.scheduled_for,
            duration_minutes=step.duration_minutes,
            target_temp_c=step.target_temp_c,
        )
        for step, timer_key in created_steps
    ]

    notes = list(brew_plan.notes)
    notes.append("Brew-plan steps were applied to timeline as pending items.")

    return BrewPlanApplyTimelineRead(
        batch_id=batch.id,
        generated_at=datetime.utcnow(),
        deleted_step_count=len(to_delete),
        preserved_step_count=len(preserved_steps),
        created_step_count=len(applied_steps),
        steps=applied_steps,
        notes=notes,
    )


@router.post("/{batch_id}/readings", response_model=FermentationReadingRead, status_code=201)
def add_fermentation_reading(
    batch_id: int,
    payload: FermentationReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FermentationReading:
    batch = _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)

    reading = FermentationReading(
        batch_id=batch.id,
        recorded_at=payload.recorded_at or datetime.utcnow(),
        gravity=payload.gravity,
        temp_c=payload.temp_c,
        ph=payload.ph,
        notes=payload.notes,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/{batch_id}/readings", response_model=list[FermentationReadingRead])
def list_fermentation_readings(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FermentationReading]:
    _get_user_batch_or_404(db, batch_id=batch_id, user_id=current_user.id)

    return (
        db.query(FermentationReading)
        .filter(FermentationReading.batch_id == batch_id)
        .order_by(FermentationReading.recorded_at.asc(), FermentationReading.id.asc())
        .all()
    )


@router.get("/{batch_id}/fermentation/trend", response_model=FermentationTrendRead)
def get_fermentation_trend(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FermentationTrendRead:
    trend = build_fermentation_trend(db, batch_id=batch_id, user_id=current_user.id)
    if trend is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return trend
