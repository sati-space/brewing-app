from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EquipmentProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=140)
    batch_volume_liters: float = Field(gt=0)
    mash_tun_volume_liters: float | None = Field(default=None, gt=0)
    boil_kettle_volume_liters: float | None = Field(default=None, gt=0)
    brewhouse_efficiency_pct: float = Field(gt=0, le=100)
    boil_off_rate_l_per_hour: float | None = Field(default=None, ge=0)
    trub_loss_liters: float | None = Field(default=None, ge=0)
    notes: str = ""


class EquipmentProfileCreate(EquipmentProfileBase):
    pass


class EquipmentProfileUpdate(EquipmentProfileBase):
    pass


class EquipmentProfileRead(EquipmentProfileBase):
    id: int
    source_provider: str
    source_external_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
