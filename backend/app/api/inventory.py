from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.inventory import InventoryItem
from app.models.user import User
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemRead,
    InventoryItemUpdate,
    LowStockAlertResponse,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


def to_inventory_read(item: InventoryItem) -> InventoryItemRead:
    return InventoryItemRead(
        id=item.id,
        name=item.name,
        ingredient_type=item.ingredient_type,
        quantity=item.quantity,
        unit=item.unit,
        low_stock_threshold=item.low_stock_threshold,
        updated_at=item.updated_at,
        is_low_stock=item.quantity <= item.low_stock_threshold,
    )


@router.post("", response_model=InventoryItemRead, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryItemRead:
    existing_item = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.owner_user_id == current_user.id,
            InventoryItem.name == payload.name,
        )
        .first()
    )
    if existing_item:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inventory item already exists")

    item = InventoryItem(
        owner_user_id=current_user.id,
        name=payload.name,
        ingredient_type=payload.ingredient_type,
        quantity=payload.quantity,
        unit=payload.unit,
        low_stock_threshold=payload.low_stock_threshold,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return to_inventory_read(item)


@router.get("", response_model=list[InventoryItemRead])
def list_inventory_items(
    low_stock_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InventoryItemRead]:
    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.owner_user_id == current_user.id)
        .order_by(InventoryItem.name.asc())
        .all()
    )

    if low_stock_only:
        items = [item for item in items if item.quantity <= item.low_stock_threshold]

    return [to_inventory_read(item) for item in items]


@router.get("/alerts/low-stock", response_model=LowStockAlertResponse)
def get_low_stock_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LowStockAlertResponse:
    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.owner_user_id == current_user.id)
        .order_by(InventoryItem.name.asc())
        .all()
    )
    low_stock_items = [to_inventory_read(item) for item in items if item.quantity <= item.low_stock_threshold]
    return LowStockAlertResponse(count=len(low_stock_items), items=low_stock_items)


@router.get("/{item_id}", response_model=InventoryItemRead)
def get_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryItemRead:
    item = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.id == item_id,
            InventoryItem.owner_user_id == current_user.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")

    return to_inventory_read(item)


@router.put("/{item_id}", response_model=InventoryItemRead)
def update_inventory_item(
    item_id: int,
    payload: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryItemRead:
    item = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.id == item_id,
            InventoryItem.owner_user_id == current_user.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")

    conflicting = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.owner_user_id == current_user.id,
            InventoryItem.name == payload.name,
            InventoryItem.id != item.id,
        )
        .first()
    )
    if conflicting:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inventory item already exists")

    item.name = payload.name
    item.ingredient_type = payload.ingredient_type
    item.quantity = payload.quantity
    item.unit = payload.unit
    item.low_stock_threshold = payload.low_stock_threshold

    db.add(item)
    db.commit()
    db.refresh(item)
    return to_inventory_read(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    item = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.id == item_id,
            InventoryItem.owner_user_id == current_user.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")

    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
