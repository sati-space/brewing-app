from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    ingredient_type: str = Field(min_length=1, max_length=30)
    quantity: float = Field(ge=0)
    unit: str = Field(min_length=1, max_length=20)
    low_stock_threshold: float = Field(default=0.0, ge=0)


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    ingredient_type: str = Field(min_length=1, max_length=30)
    quantity: float = Field(ge=0)
    unit: str = Field(min_length=1, max_length=20)
    low_stock_threshold: float = Field(default=0.0, ge=0)


class InventoryItemRead(InventoryItemBase):
    id: int
    updated_at: datetime
    is_low_stock: bool

    model_config = ConfigDict(from_attributes=True)


class LowStockAlertResponse(BaseModel):
    count: int
    items: list[InventoryItemRead]
