from __future__ import annotations

from app.schemas.batch import BrewPlanDisplayRead, BrewPlanDisplayUnitsRead, BrewPlanVolumeRead

SUPPORTED_UNIT_SYSTEMS = {"metric", "imperial"}
SUPPORTED_LANGUAGES = {"en", "es"}
SUPPORTED_TEMPERATURE_UNITS = {"C", "F"}

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "no_water_profile": "No water profile selected; water chemistry recommendation not included.",
        "water_style_unmapped": "Water recommendation skipped because the batch style is not mapped to BJCP data.",
        "inventory_cover_all": "Inventory can cover all planned ingredients for this brew day.",
        "no_hop_subs": "No hop substitutions were needed.",
        "high_calcium": "Projected calcium is well above target range; consider dilution with RO water.",
        "high_sulfate": "Projected sulfate exceeds target range; reduce gypsum or blend water.",
        "high_chloride": "Projected chloride exceeds target range; reduce calcium chloride.",
        "high_bicarbonate_start": "Starting bicarbonate is high for this style; acidification or dilution may be required.",
        "water_close": "Base water is already close to target profile; only minor adjustments may be needed.",
        "mash_water_limit": "Mash water exceeds mash tun practical limit; mash water was reduced.",
        "boil_kettle_limit": "Pre-boil volume exceeds boil kettle capacity; split boil or reduce batch size.",
        "timeline_applied": "Brew-plan steps were applied to timeline as pending items.",
        "step_heat_strike": "Heat strike water",
        "step_mash_in": "Mash in",
        "step_mash_rest": "Mash rest",
        "step_sparge": "Vorlauf and sparge",
        "step_heat_boil": "Bring wort to boil",
        "step_boil": "Boil",
        "step_chill": "Chill wort",
        "step_transfer_pitch": "Transfer and pitch yeast",
        "step_shopping": "Resolve ingredient gaps",
        "step_water_adjust": "Prepare water additions",
    },
    "es": {
        "no_water_profile": "No se selecciono perfil de agua; no se incluyo recomendacion de quimica del agua.",
        "water_style_unmapped": "Se omitio recomendacion de agua porque el estilo no esta mapeado a BJCP.",
        "inventory_cover_all": "El inventario cubre todos los ingredientes planificados para este brew day.",
        "no_hop_subs": "No se necesitaron sustituciones de luppulo.",
        "high_calcium": "El calcio proyectado esta muy por encima del rango; considera dilucion con agua RO.",
        "high_sulfate": "El sulfato proyectado excede el rango; reduce gypsum o mezcla agua.",
        "high_chloride": "El cloruro proyectado excede el rango; reduce cloruro de calcio.",
        "high_bicarbonate_start": "El bicarbonato inicial es alto para este estilo; podria requerir acidificacion o dilucion.",
        "water_close": "El agua base ya esta cerca del perfil objetivo; solo ajustes menores son necesarios.",
        "mash_water_limit": "El agua de macerado excede el limite practico del mash tun; se redujo el volumen.",
        "boil_kettle_limit": "El volumen pre-hervor excede la capacidad de la olla; divide hervor o reduce batch size.",
        "timeline_applied": "Los pasos del brew plan se aplicaron al timeline como pendientes.",
        "step_heat_strike": "Calentar agua de macerado",
        "step_mash_in": "Entrada de macerado",
        "step_mash_rest": "Descanso de macerado",
        "step_sparge": "Recirculado y lavado",
        "step_heat_boil": "Llevar mosto a hervor",
        "step_boil": "Hervor",
        "step_chill": "Enfriar mosto",
        "step_transfer_pitch": "Transferir e inocular levadura",
        "step_shopping": "Resolver faltantes de ingredientes",
        "step_water_adjust": "Preparar adiciones de agua",
    },
}


def resolve_unit_system(override: str | None, preferred: str | None) -> str:
    value = (override or preferred or "metric").lower()
    if value in SUPPORTED_UNIT_SYSTEMS:
        return value
    return "metric"


def resolve_language(override: str | None, preferred: str | None) -> str:
    value = (override or preferred or "en").lower()
    if value in SUPPORTED_LANGUAGES:
        return value
    return "en"


def resolve_temperature_unit(override: str | None, preferred: str | None, unit_system: str) -> str:
    if override and override.upper() in SUPPORTED_TEMPERATURE_UNITS:
        return override.upper()
    if preferred and preferred.upper() in SUPPORTED_TEMPERATURE_UNITS:
        return preferred.upper()
    return "F" if unit_system == "imperial" else "C"


def t(key: str, language: str) -> str:
    return _TRANSLATIONS.get(language, _TRANSLATIONS["en"]).get(key, _TRANSLATIONS["en"].get(key, key))


def to_display_units(
    *,
    unit_system: str,
    language: str,
    temperature_unit: str,
    volumes: BrewPlanVolumeRead,
) -> tuple[BrewPlanDisplayUnitsRead, BrewPlanDisplayRead]:
    temp_unit = temperature_unit.upper()
    if temp_unit not in SUPPORTED_TEMPERATURE_UNITS:
        temp_unit = "F" if unit_system == "imperial" else "C"

    def convert_temp(value_c: float) -> float:
        if temp_unit == "F":
            return round((value_c * 9.0 / 5.0) + 32.0, 2)
        return value_c

    if unit_system == "imperial":
        return (
            BrewPlanDisplayUnitsRead(
                unit_system="imperial",
                language=language,
                grain_unit="lb",
                volume_unit="gal",
                temperature_unit=temp_unit,
            ),
            BrewPlanDisplayRead(
                grain_bill=round(volumes.grain_bill_kg * 2.20462262, 3),
                mash_water=round(volumes.mash_water_liters * 0.264172052, 3),
                sparge_water=round(volumes.sparge_water_liters * 0.264172052, 3),
                total_water=round(volumes.total_water_liters * 0.264172052, 3),
                pre_boil_volume=round(volumes.pre_boil_volume_liters * 0.264172052, 3),
                post_boil_volume=round(volumes.post_boil_volume_liters * 0.264172052, 3),
                boil_off=round(volumes.estimated_boil_off_liters * 0.264172052, 3),
                mash_target_temp=convert_temp(volumes.mash_target_temp_c),
                strike_water_temp=convert_temp(volumes.strike_water_temp_c),
            ),
        )

    return (
        BrewPlanDisplayUnitsRead(
            unit_system="metric",
            language=language,
            grain_unit="kg",
            volume_unit="L",
            temperature_unit=temp_unit,
        ),
        BrewPlanDisplayRead(
            grain_bill=volumes.grain_bill_kg,
            mash_water=volumes.mash_water_liters,
            sparge_water=volumes.sparge_water_liters,
            total_water=volumes.total_water_liters,
            pre_boil_volume=volumes.pre_boil_volume_liters,
            post_boil_volume=volumes.post_boil_volume_liters,
            boil_off=volumes.estimated_boil_off_liters,
            mash_target_temp=convert_temp(volumes.mash_target_temp_c),
            strike_water_temp=convert_temp(volumes.strike_water_temp_c),
        ),
    )
