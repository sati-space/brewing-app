from __future__ import annotations

from dataclasses import dataclass

from app.models.water_profile import WaterProfile
from app.services.bjcp_styles import BJCPStyleProfile


@dataclass(frozen=True)
class MineralAddition:
    mineral_name: str
    grams_per_liter: float
    grams_total: float
    reason: str


@dataclass(frozen=True)
class WaterSnapshot:
    calcium_ppm: float
    magnesium_ppm: float
    sodium_ppm: float
    chloride_ppm: float
    sulfate_ppm: float
    bicarbonate_ppm: float


@dataclass(frozen=True)
class WaterRecommendation:
    source_profile: WaterSnapshot
    target_profile: WaterSnapshot
    projected_profile: WaterSnapshot
    additions: tuple[MineralAddition, ...]
    notes: tuple[str, ...]


_GYPSUM = {"calcium_ppm": 61.5, "sulfate_ppm": 147.4}
_CALCIUM_CHLORIDE = {"calcium_ppm": 72.0, "chloride_ppm": 127.0}
_EPSOM_SALT = {"magnesium_ppm": 26.0, "sulfate_ppm": 103.0}
_BAKING_SODA = {"sodium_ppm": 72.0, "bicarbonate_ppm": 191.7}


def build_water_recommendation(
    *,
    water_profile: WaterProfile,
    style: BJCPStyleProfile,
    batch_volume_liters: float,
) -> WaterRecommendation:
    source = _profile_snapshot(water_profile)
    target = WaterSnapshot(
        calcium_ppm=style.calcium_ppm.target_ppm,
        magnesium_ppm=style.magnesium_ppm.target_ppm,
        sodium_ppm=style.sodium_ppm.target_ppm,
        chloride_ppm=style.chloride_ppm.target_ppm,
        sulfate_ppm=style.sulfate_ppm.target_ppm,
        bicarbonate_ppm=style.bicarbonate_ppm.target_ppm,
    )
    projected = {
        "calcium_ppm": source.calcium_ppm,
        "magnesium_ppm": source.magnesium_ppm,
        "sodium_ppm": source.sodium_ppm,
        "chloride_ppm": source.chloride_ppm,
        "sulfate_ppm": source.sulfate_ppm,
        "bicarbonate_ppm": source.bicarbonate_ppm,
    }
    additions: list[MineralAddition] = []
    notes: list[str] = []

    sulfate_gap = target.sulfate_ppm - projected["sulfate_ppm"]
    if sulfate_gap > 5:
        grams_per_l = min(sulfate_gap / _GYPSUM["sulfate_ppm"], 1.5)
        _apply_addition(
            additions=additions,
            projected=projected,
            mineral_name="Gypsum (CaSO4)",
            grams_per_liter=grams_per_l,
            batch_volume_liters=batch_volume_liters,
            contribution_ppm_per_g_l=_GYPSUM,
            reason=f"Increase sulfate to sharpen bitterness for {style.name}.",
        )

    chloride_gap = target.chloride_ppm - projected["chloride_ppm"]
    if chloride_gap > 5:
        grams_per_l = min(chloride_gap / _CALCIUM_CHLORIDE["chloride_ppm"], 1.5)
        _apply_addition(
            additions=additions,
            projected=projected,
            mineral_name="Calcium Chloride (CaCl2)",
            grams_per_liter=grams_per_l,
            batch_volume_liters=batch_volume_liters,
            contribution_ppm_per_g_l=_CALCIUM_CHLORIDE,
            reason=f"Increase chloride for rounder malt balance in {style.name}.",
        )

    magnesium_gap = target.magnesium_ppm - projected["magnesium_ppm"]
    if magnesium_gap > 3:
        grams_per_l = min(magnesium_gap / _EPSOM_SALT["magnesium_ppm"], 0.6)
        _apply_addition(
            additions=additions,
            projected=projected,
            mineral_name="Epsom Salt (MgSO4)",
            grams_per_liter=grams_per_l,
            batch_volume_liters=batch_volume_liters,
            contribution_ppm_per_g_l=_EPSOM_SALT,
            reason="Increase magnesium while contributing sulfate.",
        )

    bicarbonate_gap = target.bicarbonate_ppm - projected["bicarbonate_ppm"]
    if bicarbonate_gap > 10:
        grams_per_l = min(bicarbonate_gap / _BAKING_SODA["bicarbonate_ppm"], 0.5)
        _apply_addition(
            additions=additions,
            projected=projected,
            mineral_name="Baking Soda (NaHCO3)",
            grams_per_liter=grams_per_l,
            batch_volume_liters=batch_volume_liters,
            contribution_ppm_per_g_l=_BAKING_SODA,
            reason="Raise alkalinity for mash pH support in darker beers.",
        )

    if projected["calcium_ppm"] > style.calcium_ppm.max_ppm + 40:
        notes.append("Projected calcium is well above target range; consider dilution with RO water.")
    if projected["sulfate_ppm"] > style.sulfate_ppm.max_ppm + 50:
        notes.append("Projected sulfate exceeds target range; reduce gypsum or blend water.")
    if projected["chloride_ppm"] > style.chloride_ppm.max_ppm + 40:
        notes.append("Projected chloride exceeds target range; reduce calcium chloride.")
    if source.bicarbonate_ppm > style.bicarbonate_ppm.max_ppm + 50:
        notes.append("Starting bicarbonate is high for this style; acidification or dilution may be required.")
    if not additions:
        notes.append("Base water is already close to target profile; only minor adjustments may be needed.")

    projected_snapshot = WaterSnapshot(
        calcium_ppm=round(projected["calcium_ppm"], 2),
        magnesium_ppm=round(projected["magnesium_ppm"], 2),
        sodium_ppm=round(projected["sodium_ppm"], 2),
        chloride_ppm=round(projected["chloride_ppm"], 2),
        sulfate_ppm=round(projected["sulfate_ppm"], 2),
        bicarbonate_ppm=round(projected["bicarbonate_ppm"], 2),
    )

    return WaterRecommendation(
        source_profile=source,
        target_profile=_rounded_snapshot(target),
        projected_profile=projected_snapshot,
        additions=tuple(additions),
        notes=tuple(notes),
    )


def _profile_snapshot(water_profile: WaterProfile) -> WaterSnapshot:
    return WaterSnapshot(
        calcium_ppm=round(water_profile.calcium_ppm, 2),
        magnesium_ppm=round(water_profile.magnesium_ppm, 2),
        sodium_ppm=round(water_profile.sodium_ppm, 2),
        chloride_ppm=round(water_profile.chloride_ppm, 2),
        sulfate_ppm=round(water_profile.sulfate_ppm, 2),
        bicarbonate_ppm=round(water_profile.bicarbonate_ppm, 2),
    )


def _rounded_snapshot(snapshot: WaterSnapshot) -> WaterSnapshot:
    return WaterSnapshot(
        calcium_ppm=round(snapshot.calcium_ppm, 2),
        magnesium_ppm=round(snapshot.magnesium_ppm, 2),
        sodium_ppm=round(snapshot.sodium_ppm, 2),
        chloride_ppm=round(snapshot.chloride_ppm, 2),
        sulfate_ppm=round(snapshot.sulfate_ppm, 2),
        bicarbonate_ppm=round(snapshot.bicarbonate_ppm, 2),
    )


def _apply_addition(
    *,
    additions: list[MineralAddition],
    projected: dict[str, float],
    mineral_name: str,
    grams_per_liter: float,
    batch_volume_liters: float,
    contribution_ppm_per_g_l: dict[str, float],
    reason: str,
) -> None:
    if grams_per_liter <= 0:
        return

    for ion, ppm_per_g_l in contribution_ppm_per_g_l.items():
        projected[ion] += grams_per_liter * ppm_per_g_l

    additions.append(
        MineralAddition(
            mineral_name=mineral_name,
            grams_per_liter=round(grams_per_liter, 3),
            grams_total=round(grams_per_liter * batch_volume_liters, 2),
            reason=reason,
        )
    )
