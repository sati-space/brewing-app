from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.equipment_profile import EquipmentProfile
from app.models.user import User
from app.schemas.equipment import EquipmentProfileCreate, EquipmentProfileRead, EquipmentProfileUpdate

router = APIRouter(prefix="/equipment", tags=["equipment"])


def _get_user_equipment_or_404(db: Session, equipment_id: int, user_id: int) -> EquipmentProfile:
    equipment = (
        db.query(EquipmentProfile)
        .filter(
            EquipmentProfile.id == equipment_id,
            EquipmentProfile.owner_user_id == user_id,
        )
        .first()
    )
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment profile not found")
    return equipment


@router.post("", response_model=EquipmentProfileRead, status_code=status.HTTP_201_CREATED)
def create_equipment_profile(
    payload: EquipmentProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EquipmentProfile:
    duplicate_name = (
        db.query(EquipmentProfile)
        .filter(
            EquipmentProfile.owner_user_id == current_user.id,
            EquipmentProfile.name == payload.name,
        )
        .first()
    )
    if duplicate_name:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Equipment profile already exists")

    equipment = EquipmentProfile(
        owner_user_id=current_user.id,
        source_provider="manual",
        source_external_id=str(uuid4()),
        name=payload.name,
        batch_volume_liters=payload.batch_volume_liters,
        mash_tun_volume_liters=payload.mash_tun_volume_liters,
        boil_kettle_volume_liters=payload.boil_kettle_volume_liters,
        brewhouse_efficiency_pct=payload.brewhouse_efficiency_pct,
        boil_off_rate_l_per_hour=payload.boil_off_rate_l_per_hour,
        trub_loss_liters=payload.trub_loss_liters,
        notes=payload.notes,
    )

    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.get("", response_model=list[EquipmentProfileRead])
def list_equipment_profiles(
    source_provider: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EquipmentProfile]:
    query = db.query(EquipmentProfile).filter(EquipmentProfile.owner_user_id == current_user.id)

    if source_provider:
        query = query.filter(EquipmentProfile.source_provider == source_provider)

    if search:
        like_term = f"%{search}%"
        query = query.filter(EquipmentProfile.name.ilike(like_term))

    return query.order_by(EquipmentProfile.created_at.desc(), EquipmentProfile.id.desc()).all()


@router.get("/{equipment_id}", response_model=EquipmentProfileRead)
def get_equipment_profile(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EquipmentProfile:
    return _get_user_equipment_or_404(db, equipment_id=equipment_id, user_id=current_user.id)


@router.put("/{equipment_id}", response_model=EquipmentProfileRead)
def update_equipment_profile(
    equipment_id: int,
    payload: EquipmentProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EquipmentProfile:
    equipment = _get_user_equipment_or_404(db, equipment_id=equipment_id, user_id=current_user.id)

    duplicate_name = (
        db.query(EquipmentProfile)
        .filter(
            EquipmentProfile.owner_user_id == current_user.id,
            EquipmentProfile.name == payload.name,
            EquipmentProfile.id != equipment.id,
        )
        .first()
    )
    if duplicate_name:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Equipment profile already exists")

    equipment.name = payload.name
    equipment.batch_volume_liters = payload.batch_volume_liters
    equipment.mash_tun_volume_liters = payload.mash_tun_volume_liters
    equipment.boil_kettle_volume_liters = payload.boil_kettle_volume_liters
    equipment.brewhouse_efficiency_pct = payload.brewhouse_efficiency_pct
    equipment.boil_off_rate_l_per_hour = payload.boil_off_rate_l_per_hour
    equipment.trub_loss_liters = payload.trub_loss_liters
    equipment.notes = payload.notes

    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment_profile(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    equipment = _get_user_equipment_or_404(db, equipment_id=equipment_id, user_id=current_user.id)

    db.delete(equipment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
