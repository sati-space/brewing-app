from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.models.batch import Batch
from app.models.equipment_profile import EquipmentProfile
from app.schemas.batch import (
    BatchInventoryPreviewRead,
    BatchInventoryRequirementRead,
    BrewPlanEquipmentRead,
    BrewPlanGravityRead,
    BrewPlanHopCandidateRead,
    BrewPlanHopSubstitutionRead,
    BrewPlanShoppingItemRead,
    BrewPlanStepRead,
    BrewPlanVolumeRead,
)
from app.services.hop_substitution import recommend_hop_substitutions
from app.services.preferences import t
from app.services.recipe_calculator import estimate_abv

_FERMENTABLE_TYPES = {"grain", "extract", "sugar"}
_HOP_TYPES = {"hop"}

_MASS_TO_KG = {
    "kg": 1.0,
    "g": 0.001,
    "lb": 0.453592,
    "oz": 0.0283495,
}

_UNIT_ALIASES = {
    "gram": "g",
    "grams": "g",
    "kilogram": "kg",
    "kilograms": "kg",
    "pound": "lb",
    "pounds": "lb",
    "ounce": "oz",
    "ounces": "oz",
}


@dataclass(frozen=True)
class BrewPlanResult:
    volumes: BrewPlanVolumeRead
    gravity: BrewPlanGravityRead
    equipment: BrewPlanEquipmentRead
    timer_plan: list[BrewPlanStepRead]
    shopping_list: list[BrewPlanShoppingItemRead]
    hop_substitutions: list[BrewPlanHopSubstitutionRead]
    notes: list[str]


def build_brew_day_plan(
    *,
    batch: Batch,
    inventory_preview: BatchInventoryPreviewRead,
    equipment: EquipmentProfile | None,
    snapshot_ingredients: list[dict[str, object]],
    inventory_hop_names: list[str],
    extra_available_hops: list[str],
    brew_start_at: datetime | None,
    language: str,
) -> BrewPlanResult:
    notes: list[str] = []
    equipment_summary = _build_equipment_summary(equipment=equipment)
    grain_bill_kg = _sum_grain_bill_kg(snapshot_ingredients)
    style_token = (batch.recipe_style_snapshot or "").lower()
    source_og = float(batch.recipe_target_og_snapshot or 1.050)
    source_fg = float(batch.recipe_target_fg_snapshot or 1.012)
    source_efficiency_pct = float(batch.recipe_efficiency_pct_snapshot or 70.0)
    target_efficiency_pct = equipment.brewhouse_efficiency_pct if equipment else source_efficiency_pct

    fermentable_coverage = _fermentable_coverage(inventory_preview.requirements)
    adjusted_og = _estimate_adjusted_og(
        source_og=source_og,
        source_efficiency_pct=source_efficiency_pct,
        target_efficiency_pct=target_efficiency_pct,
        fermentable_coverage=fermentable_coverage,
    )
    adjusted_fg = _estimate_adjusted_fg(source_og=source_og, source_fg=source_fg, adjusted_og=adjusted_og)

    mash_temp_c = _choose_mash_temp(style_token=style_token)
    mash_rest_minutes = _choose_mash_rest_minutes(style_token=style_token, source_og=source_og)
    mash_ratio_l_per_kg = 2.8 if source_og >= 1.070 else 2.7
    mash_water_liters = round(grain_bill_kg * mash_ratio_l_per_kg, 2)

    if equipment and equipment.mash_tun_volume_liters:
        max_mash_water = round(equipment.mash_tun_volume_liters * 0.9, 2)
        if mash_water_liters > max_mash_water and max_mash_water > 0:
            notes.append(t("mash_water_limit", language))
            mash_water_liters = max_mash_water

    grain_absorption_liters = round(grain_bill_kg * 0.8, 2)
    first_runnings_liters = max(mash_water_liters - grain_absorption_liters, 0.0)
    boil_minutes = 75 if "lager" in style_token else 60
    boil_off_rate_l_per_hour = equipment.boil_off_rate_l_per_hour if equipment and equipment.boil_off_rate_l_per_hour else 3.0
    trub_loss_liters = equipment.trub_loss_liters if equipment and equipment.trub_loss_liters else 1.0
    estimated_boil_off_liters = round(boil_off_rate_l_per_hour * (boil_minutes / 60.0), 2)
    pre_boil_volume_liters = round(batch.volume_liters + trub_loss_liters + estimated_boil_off_liters, 2)
    sparge_water_liters = round(max(pre_boil_volume_liters - first_runnings_liters, 0.0), 2)
    total_water_liters = round(mash_water_liters + sparge_water_liters, 2)

    if equipment and equipment.boil_kettle_volume_liters and pre_boil_volume_liters > equipment.boil_kettle_volume_liters:
        notes.append(t("boil_kettle_limit", language))

    strike_temp_c = _estimate_strike_temp(mash_temp_c=mash_temp_c, mash_ratio_l_per_kg=mash_ratio_l_per_kg)
    sparge_minutes = _estimate_sparge_minutes(sparge_water_liters=sparge_water_liters)
    timer_plan = _build_timer_plan(
        grain_bill_kg=grain_bill_kg,
        mash_water_liters=mash_water_liters,
        pre_boil_volume_liters=pre_boil_volume_liters,
        mash_temp_c=mash_temp_c,
        strike_temp_c=strike_temp_c,
        mash_rest_minutes=mash_rest_minutes,
        sparge_minutes=sparge_minutes,
        boil_minutes=boil_minutes,
        brew_start_at=brew_start_at,
        language=language,
    )

    available_hops = [name for name in [*extra_available_hops, *inventory_hop_names] if name.strip()]
    shopping_list, substitutions = _build_shopping_and_substitutions(
        requirements=inventory_preview.requirements,
        available_hop_names=available_hops,
    )

    if not shopping_list:
        notes.append(t("inventory_cover_all", language))
    if not substitutions:
        notes.append(t("no_hop_subs", language))

    volumes = BrewPlanVolumeRead(
        grain_bill_kg=round(grain_bill_kg, 3),
        mash_water_liters=mash_water_liters,
        sparge_water_liters=sparge_water_liters,
        total_water_liters=total_water_liters,
        pre_boil_volume_liters=pre_boil_volume_liters,
        post_boil_volume_liters=round(batch.volume_liters, 2),
        estimated_boil_off_liters=estimated_boil_off_liters,
        mash_target_temp_c=round(mash_temp_c, 1),
        strike_water_temp_c=round(strike_temp_c, 1),
        mash_rest_minutes=mash_rest_minutes,
        sparge_minutes=sparge_minutes,
        boil_minutes=boil_minutes,
    )
    gravity = BrewPlanGravityRead(
        source_target_og=round(source_og, 3),
        source_target_fg=round(source_fg, 3),
        estimated_og=round(adjusted_og, 3),
        estimated_fg=round(adjusted_fg, 3),
        estimated_abv=estimate_abv(round(adjusted_og, 3), round(adjusted_fg, 3)),
        fermentable_inventory_coverage_pct=round(fermentable_coverage * 100, 2),
        source_efficiency_pct=round(source_efficiency_pct, 2),
        target_efficiency_pct=round(target_efficiency_pct, 2),
    )

    return BrewPlanResult(
        volumes=volumes,
        gravity=gravity,
        equipment=equipment_summary,
        timer_plan=timer_plan,
        shopping_list=shopping_list,
        hop_substitutions=substitutions,
        notes=notes,
    )


def _build_equipment_summary(equipment: EquipmentProfile | None) -> BrewPlanEquipmentRead:
    if equipment is None:
        return BrewPlanEquipmentRead(
            equipment_profile_id=None,
            equipment_name=None,
            batch_volume_liters=None,
            mash_tun_volume_liters=None,
            boil_kettle_volume_liters=None,
            boil_off_rate_l_per_hour=3.0,
            trub_loss_liters=1.0,
        )

    return BrewPlanEquipmentRead(
        equipment_profile_id=equipment.id,
        equipment_name=equipment.name,
        batch_volume_liters=round(equipment.batch_volume_liters, 2),
        mash_tun_volume_liters=round(equipment.mash_tun_volume_liters, 2) if equipment.mash_tun_volume_liters else None,
        boil_kettle_volume_liters=round(equipment.boil_kettle_volume_liters, 2) if equipment.boil_kettle_volume_liters else None,
        boil_off_rate_l_per_hour=round(equipment.boil_off_rate_l_per_hour, 2) if equipment.boil_off_rate_l_per_hour else 3.0,
        trub_loss_liters=round(equipment.trub_loss_liters, 2) if equipment.trub_loss_liters else 1.0,
    )


def _sum_grain_bill_kg(snapshot_ingredients: list[dict[str, object]]) -> float:
    total_kg = 0.0
    for ingredient in snapshot_ingredients:
        ingredient_type = str(ingredient.get("ingredient_type", "")).strip().lower()
        if ingredient_type not in _FERMENTABLE_TYPES:
            continue
        amount = _safe_float(ingredient.get("amount"))
        unit = str(ingredient.get("unit", "")).strip().lower()
        unit = _UNIT_ALIASES.get(unit, unit)
        factor = _MASS_TO_KG.get(unit)
        if amount is None or factor is None or amount <= 0:
            continue
        total_kg += amount * factor
    return total_kg


def _fermentable_coverage(requirements: list[BatchInventoryRequirementRead]) -> float:
    fermentables = [row for row in requirements if row.ingredient_type.strip().lower() in _FERMENTABLE_TYPES]
    if not fermentables:
        return 1.0

    required_total = sum(max(row.required_amount, 0.0) for row in fermentables)
    if required_total <= 0:
        return 1.0
    covered_total = sum(min(max(row.available_amount, 0.0), max(row.required_amount, 0.0)) for row in fermentables)
    return max(0.0, min(covered_total / required_total, 1.0))


def _estimate_adjusted_og(
    *,
    source_og: float,
    source_efficiency_pct: float,
    target_efficiency_pct: float,
    fermentable_coverage: float,
) -> float:
    source_points = max((source_og - 1.0) * 1000.0, 1.0)
    efficiency_ratio = target_efficiency_pct / source_efficiency_pct if source_efficiency_pct > 0 else 1.0
    adjusted_points = source_points * efficiency_ratio * fermentable_coverage
    return 1.0 + (adjusted_points / 1000.0)


def _estimate_adjusted_fg(*, source_og: float, source_fg: float, adjusted_og: float) -> float:
    source_points = max((source_og - 1.0) * 1000.0, 0.0001)
    attenuation = max(min((source_og - source_fg) * 1000.0 / source_points, 1.0), 0.0)
    return adjusted_og - attenuation * (adjusted_og - 1.0)


def _choose_mash_temp(*, style_token: str) -> float:
    if "stout" in style_token or "porter" in style_token:
        return 67.5
    if "lager" in style_token or "pils" in style_token:
        return 65.5
    if "hazy" in style_token:
        return 67.0
    if "ipa" in style_token or "pale" in style_token:
        return 66.0
    return 66.5


def _choose_mash_rest_minutes(*, style_token: str, source_og: float) -> int:
    minutes = 60
    if "lager" in style_token:
        minutes += 10
    if source_og >= 1.070:
        minutes += 10
    return minutes


def _estimate_strike_temp(*, mash_temp_c: float, mash_ratio_l_per_kg: float) -> float:
    ratio_qt_lb = max(mash_ratio_l_per_kg / 2.086, 0.8)
    grain_temp_c = 20.0
    return ((0.41 / ratio_qt_lb) * (mash_temp_c - grain_temp_c)) + mash_temp_c


def _estimate_sparge_minutes(*, sparge_water_liters: float) -> int:
    return max(15, min(45, int(round(10 + (sparge_water_liters * 1.6)))))


def _build_timer_plan(
    *,
    grain_bill_kg: float,
    mash_water_liters: float,
    pre_boil_volume_liters: float,
    mash_temp_c: float,
    strike_temp_c: float,
    mash_rest_minutes: int,
    sparge_minutes: int,
    boil_minutes: int,
    brew_start_at: datetime | None,
    language: str,
) -> list[BrewPlanStepRead]:
    steps: list[tuple[str, str, int, float | None]] = []

    if grain_bill_kg > 0 and mash_water_liters > 0:
        heat_minutes = max(15, min(55, int(round(mash_water_liters * 1.7))))
        steps.extend(
            [
                ("heat_strike", t("step_heat_strike", language), heat_minutes, strike_temp_c),
                ("mash_in", t("step_mash_in", language), 10, mash_temp_c),
                ("mash_rest", t("step_mash_rest", language), mash_rest_minutes, mash_temp_c),
                ("sparge", t("step_sparge", language), sparge_minutes, 76.0),
            ]
        )

    bring_to_boil_minutes = max(15, min(50, int(round(max(pre_boil_volume_liters, 5.0) * 1.2))))
    steps.extend(
        [
            ("heat_boil", t("step_heat_boil", language), bring_to_boil_minutes, 100.0),
            ("boil", t("step_boil", language), boil_minutes, 100.0),
            ("chill", t("step_chill", language), 20, 20.0),
            ("transfer_pitch", t("step_transfer_pitch", language), 15, None),
        ]
    )

    timer_steps: list[BrewPlanStepRead] = []
    offset = 0
    for index, (timer_key, name, duration, target_temp) in enumerate(steps, start=1):
        planned_start = brew_start_at + timedelta(minutes=offset) if brew_start_at else None
        planned_end = brew_start_at + timedelta(minutes=offset + duration) if brew_start_at else None
        timer_steps.append(
            BrewPlanStepRead(
                step_order=index,
                timer_key=timer_key,
                name=name,
                duration_minutes=duration,
                target_temp_c=round(target_temp, 1) if target_temp is not None else None,
                start_offset_minutes=offset,
                planned_start_at=planned_start,
                planned_end_at=planned_end,
            )
        )
        offset += duration

    return timer_steps


def _build_shopping_and_substitutions(
    *,
    requirements: list[BatchInventoryRequirementRead],
    available_hop_names: list[str],
) -> tuple[list[BrewPlanShoppingItemRead], list[BrewPlanHopSubstitutionRead]]:
    shopping: list[BrewPlanShoppingItemRead] = []
    substitutions: list[BrewPlanHopSubstitutionRead] = []

    for requirement in requirements:
        if requirement.enough_stock:
            continue

        suggested_names: list[str] = []
        hop_candidates: list[BrewPlanHopCandidateRead] = []
        if requirement.ingredient_type.strip().lower() in _HOP_TYPES:
            try:
                result = recommend_hop_substitutions(
                    target_hop_name=requirement.name,
                    available_hop_names=available_hop_names,
                    top_k=3,
                )
                hop_candidates = [
                    BrewPlanHopCandidateRead(
                        name=candidate.name,
                        similarity_score=candidate.similarity_score,
                        recommended_bittering_ratio=candidate.recommended_bittering_ratio,
                        shared_descriptors=list(candidate.shared_descriptors),
                    )
                    for candidate in result.substitutions
                ]
                suggested_names = [candidate.name for candidate in hop_candidates]
            except ValueError:
                hop_candidates = []
                suggested_names = []

        shopping.append(
            BrewPlanShoppingItemRead(
                name=requirement.name,
                ingredient_type=requirement.ingredient_type,
                required_amount=requirement.required_amount,
                required_unit=requirement.required_unit,
                available_amount=requirement.available_amount,
                shortage_amount=requirement.shortage_amount,
                suggested_substitutions=suggested_names,
            )
        )

        if hop_candidates:
            substitutions.append(
                BrewPlanHopSubstitutionRead(
                    target_hop_name=requirement.name,
                    missing_amount=requirement.shortage_amount,
                    unit=requirement.required_unit,
                    candidates=hop_candidates,
                )
            )

    return shopping, substitutions


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
