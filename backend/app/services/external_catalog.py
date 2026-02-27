from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalRecipeIngredientTemplate:
    name: str
    ingredient_type: str
    amount: float
    unit: str
    stage: str
    minute_added: int


@dataclass(frozen=True)
class ExternalRecipeTemplate:
    provider: str
    external_id: str
    name: str
    style: str
    target_og: float
    target_fg: float
    target_ibu: float
    target_srm: float
    efficiency_pct: float
    notes: str
    ingredients: tuple[ExternalRecipeIngredientTemplate, ...]


@dataclass(frozen=True)
class ExternalEquipmentTemplate:
    provider: str
    external_id: str
    name: str
    batch_volume_liters: float
    mash_tun_volume_liters: float | None
    boil_kettle_volume_liters: float | None
    brewhouse_efficiency_pct: float
    boil_off_rate_l_per_hour: float | None
    trub_loss_liters: float | None
    notes: str


@dataclass(frozen=True)
class ExternalIngredientTemplate:
    provider: str
    external_id: str
    name: str
    ingredient_type: str
    default_unit: str
    notes: str


_RECIPE_TEMPLATES: tuple[ExternalRecipeTemplate, ...] = (
    ExternalRecipeTemplate(
        provider="brewbench",
        external_id="snpa-clone-v1",
        name="Sierra Nevada Pale Ale Clone",
        style="18B",
        target_og=1.052,
        target_fg=1.011,
        target_ibu=38,
        target_srm=9,
        efficiency_pct=74,
        notes="Classic US pale ale profile with late cascade additions.",
        ingredients=(
            ExternalRecipeIngredientTemplate("Pale Malt", "grain", 4.5, "kg", "mash", 0),
            ExternalRecipeIngredientTemplate("Crystal 60", "grain", 0.35, "kg", "mash", 0),
            ExternalRecipeIngredientTemplate("Cascade", "hop", 20, "g", "boil", 60),
            ExternalRecipeIngredientTemplate("Cascade", "hop", 25, "g", "boil", 10),
            ExternalRecipeIngredientTemplate("US-05", "yeast", 1, "pack", "fermentation", 0),
        ),
    ),
    ExternalRecipeTemplate(
        provider="brewbench",
        external_id="dry-stout-v1",
        name="Dry Irish Stout Template",
        style="15B",
        target_og=1.044,
        target_fg=1.010,
        target_ibu=35,
        target_srm=35,
        efficiency_pct=72,
        notes="Roasty session stout template with firm bitterness.",
        ingredients=(
            ExternalRecipeIngredientTemplate("Pale Malt", "grain", 3.4, "kg", "mash", 0),
            ExternalRecipeIngredientTemplate("Flaked Barley", "grain", 0.45, "kg", "mash", 0),
            ExternalRecipeIngredientTemplate("Roasted Barley", "grain", 0.35, "kg", "mash", 0),
            ExternalRecipeIngredientTemplate("East Kent Goldings", "hop", 35, "g", "boil", 60),
            ExternalRecipeIngredientTemplate("S-04", "yeast", 1, "pack", "fermentation", 0),
        ),
    ),
    ExternalRecipeTemplate(
        provider="craftdb",
        external_id="west-coast-ipa-v2",
        name="West Coast IPA Starter",
        style="21A",
        target_og=1.062,
        target_fg=1.010,
        target_ibu=62,
        target_srm=7,
        efficiency_pct=75,
        notes="Dry, bitter IPA base recipe with modern whirlpool hops.",
        ingredients=(
            ExternalRecipeIngredientTemplate("Pale Malt", "grain", 5.2, "kg", "mash", 0),
            ExternalRecipeIngredientTemplate("Munich Malt", "grain", 0.4, "kg", "mash", 0),
            ExternalRecipeIngredientTemplate("Columbus", "hop", 20, "g", "boil", 60),
            ExternalRecipeIngredientTemplate("Citra", "hop", 60, "g", "boil", 10),
            ExternalRecipeIngredientTemplate("US-05", "yeast", 1, "pack", "fermentation", 0),
        ),
    ),
    ExternalRecipeTemplate(
        provider="brewbench",
        external_id="torpedo-extra-ipa-clone-v1",
        name="Sierra Nevada Torpedo Extra IPA Clone",
        style="21A",
        target_og=1.065,
        target_fg=1.013,
        target_ibu=64,
        target_srm=8,
        efficiency_pct=74,
        notes="Clone-style template inspired by Torpedo Extra IPA with Magnum, Crystal, and Citra hops.",
        ingredients=(
            ExternalRecipeIngredientTemplate("Pale Malt", "grain", 5.3, "kg", "mash", 0),
            ExternalRecipeIngredientTemplate("Crystal 40", "grain", 0.45, "kg", "mash", 0),
            ExternalRecipeIngredientTemplate("Magnum", "hop", 18, "g", "boil", 60),
            ExternalRecipeIngredientTemplate("Crystal", "hop", 28, "g", "boil", 15),
            ExternalRecipeIngredientTemplate("Citra", "hop", 45, "g", "boil", 5),
            ExternalRecipeIngredientTemplate("US-05", "yeast", 1, "pack", "fermentation", 0),
        ),
    ),
)


_EQUIPMENT_TEMPLATES: tuple[ExternalEquipmentTemplate, ...] = (
    ExternalEquipmentTemplate(
        provider="brewbench",
        external_id="all-grain-20l-cooler",
        name="All-Grain 20L Cooler Setup",
        batch_volume_liters=20.0,
        mash_tun_volume_liters=28.0,
        boil_kettle_volume_liters=35.0,
        brewhouse_efficiency_pct=72.0,
        boil_off_rate_l_per_hour=3.2,
        trub_loss_liters=1.2,
        notes="Single-infusion cooler mash tun with propane boil kettle.",
    ),
    ExternalEquipmentTemplate(
        provider="craftdb",
        external_id="biab-electric-35l",
        name="Electric BIAB 35L",
        batch_volume_liters=23.0,
        mash_tun_volume_liters=35.0,
        boil_kettle_volume_liters=35.0,
        brewhouse_efficiency_pct=70.0,
        boil_off_rate_l_per_hour=2.8,
        trub_loss_liters=1.0,
        notes="Single-vessel BIAB profile optimized for compact electric systems.",
    ),
)


_INGREDIENT_TEMPLATES: tuple[ExternalIngredientTemplate, ...] = (
    ExternalIngredientTemplate(
        provider="brewbench",
        external_id="ing-pale-malt",
        name="Pale Malt",
        ingredient_type="grain",
        default_unit="kg",
        notes="Base malt for pale ales, lagers, and most clean ale recipes.",
    ),
    ExternalIngredientTemplate(
        provider="brewbench",
        external_id="ing-crystal-60",
        name="Crystal 60",
        ingredient_type="grain",
        default_unit="kg",
        notes="Caramel malt for color and residual sweetness.",
    ),
    ExternalIngredientTemplate(
        provider="brewbench",
        external_id="ing-cascade",
        name="Cascade",
        ingredient_type="hop",
        default_unit="g",
        notes="Classic US hop with citrus and floral profile.",
    ),
    ExternalIngredientTemplate(
        provider="craftdb",
        external_id="ing-us05",
        name="US-05",
        ingredient_type="yeast",
        default_unit="pack",
        notes="Neutral American ale yeast with high attenuation.",
    ),
    ExternalIngredientTemplate(
        provider="craftdb",
        external_id="ing-eKG",
        name="East Kent Goldings",
        ingredient_type="hop",
        default_unit="g",
        notes="Traditional English aroma hop with earthy/floral character.",
    ),
    ExternalIngredientTemplate(
        provider="brewbench",
        external_id="ing-citra",
        name="Citra",
        ingredient_type="hop",
        default_unit="g",
        notes="High-impact US hop with citrus and tropical fruit aroma.",
    ),
    ExternalIngredientTemplate(
        provider="brewbench",
        external_id="ing-magnum",
        name="Magnum",
        ingredient_type="hop",
        default_unit="g",
        notes="Clean high-alpha bittering hop used across many IPA recipes.",
    ),
    ExternalIngredientTemplate(
        provider="brewbench",
        external_id="ing-crystal-hop",
        name="Crystal",
        ingredient_type="hop",
        default_unit="g",
        notes="Aroma-forward hop with floral and mild spicy notes.",
    ),
)


def _matches(text: str, search: str | None) -> bool:
    if not search:
        return True
    return search.lower() in text.lower()


def list_recipe_templates(provider: str | None = None, search: str | None = None) -> list[ExternalRecipeTemplate]:
    items = [
        template
        for template in _RECIPE_TEMPLATES
        if (provider is None or template.provider == provider)
        and (_matches(template.name, search) or _matches(template.style, search))
    ]
    items.sort(key=lambda item: (item.provider, item.name))
    return items


def get_recipe_template(provider: str, external_id: str) -> ExternalRecipeTemplate | None:
    for template in _RECIPE_TEMPLATES:
        if template.provider == provider and template.external_id == external_id:
            return template
    return None


def list_equipment_templates(provider: str | None = None, search: str | None = None) -> list[ExternalEquipmentTemplate]:
    items = [
        template
        for template in _EQUIPMENT_TEMPLATES
        if (provider is None or template.provider == provider)
        and _matches(template.name, search)
    ]
    items.sort(key=lambda item: (item.provider, item.name))
    return items


def get_equipment_template(provider: str, external_id: str) -> ExternalEquipmentTemplate | None:
    for template in _EQUIPMENT_TEMPLATES:
        if template.provider == provider and template.external_id == external_id:
            return template
    return None


def list_ingredient_templates(
    provider: str | None = None,
    ingredient_type: str | None = None,
    search: str | None = None,
) -> list[ExternalIngredientTemplate]:
    items = [
        template
        for template in _INGREDIENT_TEMPLATES
        if (provider is None or template.provider == provider)
        and (ingredient_type is None or template.ingredient_type == ingredient_type)
        and (_matches(template.name, search) or _matches(template.notes, search))
    ]
    items.sort(key=lambda item: (item.provider, item.ingredient_type, item.name))
    return items


def get_ingredient_template(provider: str, external_id: str) -> ExternalIngredientTemplate | None:
    for template in _INGREDIENT_TEMPLATES:
        if template.provider == provider and template.external_id == external_id:
            return template
    return None
