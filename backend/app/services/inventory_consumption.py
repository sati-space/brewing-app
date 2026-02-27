from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.inventory import InventoryItem
from app.schemas.batch import (
    BatchInventoryConsumeItemRead,
    BatchInventoryConsumeRead,
    BatchInventoryPreviewRead,
    BatchInventoryRequirementRead,
)
from app.services.batch_snapshot import parse_snapshot_ingredients

_UNIT_FACTORS_TO_BASE: dict[str, tuple[str, float]] = {
    "g": ("mass", 1.0),
    "kg": ("mass", 1000.0),
    "oz": ("mass", 28.3495),
    "lb": ("mass", 453.592),
    "ml": ("volume", 1.0),
    "l": ("volume", 1000.0),
    "floz": ("volume", 29.5735),
    "qt": ("volume", 946.353),
    "gal": ("volume", 3785.41),
    "pack": ("count", 1.0),
    "each": ("count", 1.0),
    "unit": ("count", 1.0),
}

_UNIT_ALIASES: dict[str, str] = {
    "gram": "g",
    "grams": "g",
    "kgs": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "ounce": "oz",
    "ounces": "oz",
    "pound": "lb",
    "pounds": "lb",
    "liter": "l",
    "liters": "l",
    "litre": "l",
    "litres": "l",
    "fl oz": "floz",
    "fluid ounce": "floz",
    "fluid ounces": "floz",
    "floz": "floz",
    "quart": "qt",
    "quarts": "qt",
    "gallon": "gal",
    "gallons": "gal",
    "milliliter": "ml",
    "milliliters": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "packs": "pack",
}


@dataclass
class _Requirement:
    name: str
    ingredient_type: str
    amount: float
    unit: str


def _canonical_unit(unit: str) -> str:
    lowered = unit.strip().lower()
    if lowered in _UNIT_ALIASES:
        return _UNIT_ALIASES[lowered]
    return lowered


def _convert_amount(amount: float, from_unit: str, to_unit: str) -> float | None:
    from_canonical = _canonical_unit(from_unit)
    to_canonical = _canonical_unit(to_unit)

    if from_canonical == to_canonical:
        return amount

    from_meta = _UNIT_FACTORS_TO_BASE.get(from_canonical)
    to_meta = _UNIT_FACTORS_TO_BASE.get(to_canonical)
    if not from_meta or not to_meta:
        return None

    from_group, from_factor = from_meta
    to_group, to_factor = to_meta
    if from_group != to_group:
        return None

    value_in_base = amount * from_factor
    return value_in_base / to_factor


def _round(value: float) -> float:
    return round(value, 4)


def _build_requirements(batch: Batch) -> list[_Requirement]:
    raw_ingredients = parse_snapshot_ingredients(batch)

    aggregated: dict[tuple[str, str, str], _Requirement] = {}
    for ingredient in raw_ingredients:
        name = str(ingredient.get("name", "")).strip()
        ingredient_type = str(ingredient.get("ingredient_type", "")).strip()
        unit = str(ingredient.get("unit", "")).strip()

        if not name or not unit:
            continue

        try:
            amount = float(ingredient.get("amount", 0.0))
        except (TypeError, ValueError):
            continue

        if amount <= 0:
            continue

        key = (name.lower(), ingredient_type.lower(), unit.lower())
        existing = aggregated.get(key)
        if existing is None:
            aggregated[key] = _Requirement(
                name=name,
                ingredient_type=ingredient_type,
                amount=amount,
                unit=unit,
            )
        else:
            existing.amount += amount

    requirements = list(aggregated.values())
    requirements.sort(key=lambda requirement: (requirement.name.lower(), requirement.unit.lower()))
    return requirements


def _failure_result(
    batch_id: int,
    detail: str,
    *,
    consumed_at: datetime | None = None,
    shortage_count: int = 0,
    shortages: list[BatchInventoryRequirementRead] | None = None,
) -> BatchInventoryConsumeRead:
    return BatchInventoryConsumeRead(
        batch_id=batch_id,
        consumed=False,
        consumed_at=consumed_at,
        shortage_count=shortage_count,
        items=[],
        shortages=shortages or [],
        detail=detail,
    )


def build_inventory_preview(db: Session, batch: Batch, user_id: int) -> BatchInventoryPreviewRead:
    requirements = _build_requirements(batch)

    inventory_items = (
        db.query(InventoryItem)
        .filter(InventoryItem.owner_user_id == user_id)
        .all()
    )
    inventory_by_name = {
        item.name.strip().lower(): item
        for item in inventory_items
    }

    preview_rows: list[BatchInventoryRequirementRead] = []
    shortage_count = 0

    for requirement in requirements:
        matched_inventory = inventory_by_name.get(requirement.name.strip().lower())
        available_amount = 0.0
        shortage_amount = requirement.amount
        enough_stock = False
        inventory_item_id: int | None = None
        inventory_unit: str | None = None

        if matched_inventory:
            converted_available = _convert_amount(
                amount=matched_inventory.quantity,
                from_unit=matched_inventory.unit,
                to_unit=requirement.unit,
            )

            inventory_item_id = matched_inventory.id
            inventory_unit = matched_inventory.unit

            if converted_available is not None:
                available_amount = converted_available
                shortage_amount = max(requirement.amount - converted_available, 0.0)
                enough_stock = shortage_amount <= 0.0001

        if not enough_stock:
            shortage_count += 1

        preview_rows.append(
            BatchInventoryRequirementRead(
                name=requirement.name,
                ingredient_type=requirement.ingredient_type,
                required_amount=_round(requirement.amount),
                required_unit=requirement.unit,
                available_amount=_round(available_amount),
                shortage_amount=_round(shortage_amount),
                enough_stock=enough_stock,
                inventory_item_id=inventory_item_id,
                inventory_unit=inventory_unit,
            )
        )

    can_consume = bool(preview_rows) and shortage_count == 0

    return BatchInventoryPreviewRead(
        batch_id=batch.id,
        can_consume=can_consume,
        shortage_count=shortage_count,
        requirements=preview_rows,
    )


def consume_inventory_for_batch(db: Session, batch: Batch, user_id: int) -> BatchInventoryConsumeRead:
    if batch.inventory_consumed_at is not None:
        return _failure_result(
            batch_id=batch.id,
            detail="Inventory already consumed for this batch.",
            consumed_at=batch.inventory_consumed_at,
        )

    preview = build_inventory_preview(db, batch=batch, user_id=user_id)
    if not preview.requirements:
        return _failure_result(
            batch_id=batch.id,
            detail="No snapshot ingredients available for this batch.",
        )

    shortages = [row for row in preview.requirements if not row.enough_stock]
    if shortages:
        return _failure_result(
            batch_id=batch.id,
            detail="Insufficient inventory to consume this batch.",
            shortage_count=preview.shortage_count,
            shortages=shortages,
        )

    inventory_items = (
        db.query(InventoryItem)
        .filter(InventoryItem.owner_user_id == user_id)
        .all()
    )
    inventory_by_id = {item.id: item for item in inventory_items}

    planned_deductions: list[tuple[InventoryItem, BatchInventoryRequirementRead, float]] = []
    for requirement in preview.requirements:
        inventory_item_id = requirement.inventory_item_id
        if inventory_item_id is None:
            return _failure_result(batch_id=batch.id, detail="Missing inventory mapping for requirement.")

        inventory_item = inventory_by_id.get(inventory_item_id)
        if inventory_item is None:
            return _failure_result(batch_id=batch.id, detail="Inventory item was not found during consumption.")

        deduction = _convert_amount(
            amount=requirement.required_amount,
            from_unit=requirement.required_unit,
            to_unit=inventory_item.unit,
        )
        if deduction is None:
            return _failure_result(batch_id=batch.id, detail="Incompatible units during inventory consumption.")

        planned_deductions.append((inventory_item, requirement, deduction))

    consumed_items: list[BatchInventoryConsumeItemRead] = []
    for inventory_item, requirement, deduction in planned_deductions:
        quantity_before = inventory_item.quantity
        quantity_after = quantity_before - deduction
        if quantity_after < 0 and abs(quantity_after) <= 0.0001:
            quantity_after = 0.0

        quantity_after = round(quantity_after, 6)
        inventory_item.quantity = quantity_after

        consumed_items.append(
            BatchInventoryConsumeItemRead(
                inventory_item_id=inventory_item.id,
                name=inventory_item.name,
                consumed_amount=_round(deduction),
                consumed_unit=inventory_item.unit,
                quantity_before=_round(quantity_before),
                quantity_after=_round(inventory_item.quantity),
            )
        )

    consumed_at = datetime.utcnow()
    batch.inventory_consumed_at = consumed_at

    db.add(batch)
    db.commit()
    db.refresh(batch)

    return BatchInventoryConsumeRead(
        batch_id=batch.id,
        consumed=True,
        consumed_at=batch.inventory_consumed_at,
        shortage_count=0,
        items=consumed_items,
        shortages=[],
        detail="Inventory consumed successfully for batch.",
    )
