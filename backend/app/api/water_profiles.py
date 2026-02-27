from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.recipe import Recipe
from app.models.user import User
from app.models.water_profile import WaterProfile
from app.schemas.water import (
    MineralAdditionRead,
    WaterIonSnapshotRead,
    WaterProfileCreate,
    WaterProfileRead,
    WaterProfileUpdate,
    WaterRecommendationRead,
    WaterRecommendationRequest,
)
from app.services.bjcp_styles import resolve_bjcp_style
from app.services.water_recommendation import build_water_recommendation

router = APIRouter(prefix="/water-profiles", tags=["water"])


def _get_user_water_profile_or_404(db: Session, water_profile_id: int, user_id: int) -> WaterProfile:
    water_profile = (
        db.query(WaterProfile)
        .filter(
            WaterProfile.id == water_profile_id,
            WaterProfile.owner_user_id == user_id,
        )
        .first()
    )
    if not water_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Water profile not found")
    return water_profile


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.post("", response_model=WaterProfileRead, status_code=status.HTTP_201_CREATED)
def create_water_profile(
    payload: WaterProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WaterProfile:
    duplicate = (
        db.query(WaterProfile)
        .filter(
            WaterProfile.owner_user_id == current_user.id,
            WaterProfile.name == payload.name,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Water profile already exists")

    water_profile = WaterProfile(
        owner_user_id=current_user.id,
        name=payload.name,
        calcium_ppm=payload.calcium_ppm,
        magnesium_ppm=payload.magnesium_ppm,
        sodium_ppm=payload.sodium_ppm,
        chloride_ppm=payload.chloride_ppm,
        sulfate_ppm=payload.sulfate_ppm,
        bicarbonate_ppm=payload.bicarbonate_ppm,
        notes=payload.notes,
    )
    db.add(water_profile)
    db.commit()
    db.refresh(water_profile)
    return water_profile


@router.get("", response_model=list[WaterProfileRead])
def list_water_profiles(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WaterProfile]:
    query = db.query(WaterProfile).filter(WaterProfile.owner_user_id == current_user.id)
    if search:
        query = query.filter(WaterProfile.name.ilike(f"%{search}%"))
    return query.order_by(WaterProfile.name.asc()).all()


@router.get("/{water_profile_id}", response_model=WaterProfileRead)
def get_water_profile(
    water_profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WaterProfile:
    return _get_user_water_profile_or_404(db, water_profile_id=water_profile_id, user_id=current_user.id)


@router.put("/{water_profile_id}", response_model=WaterProfileRead)
def update_water_profile(
    water_profile_id: int,
    payload: WaterProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WaterProfile:
    water_profile = _get_user_water_profile_or_404(db, water_profile_id=water_profile_id, user_id=current_user.id)
    duplicate = (
        db.query(WaterProfile)
        .filter(
            WaterProfile.owner_user_id == current_user.id,
            WaterProfile.name == payload.name,
            WaterProfile.id != water_profile.id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Water profile already exists")

    water_profile.name = payload.name
    water_profile.calcium_ppm = payload.calcium_ppm
    water_profile.magnesium_ppm = payload.magnesium_ppm
    water_profile.sodium_ppm = payload.sodium_ppm
    water_profile.chloride_ppm = payload.chloride_ppm
    water_profile.sulfate_ppm = payload.sulfate_ppm
    water_profile.bicarbonate_ppm = payload.bicarbonate_ppm
    water_profile.notes = payload.notes

    db.add(water_profile)
    db.commit()
    db.refresh(water_profile)
    return water_profile


@router.delete("/{water_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_water_profile(
    water_profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    water_profile = _get_user_water_profile_or_404(db, water_profile_id=water_profile_id, user_id=current_user.id)
    db.delete(water_profile)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{water_profile_id}/recommendations", response_model=WaterRecommendationRead)
def recommend_water_adjustments(
    water_profile_id: int,
    payload: WaterRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WaterRecommendationRead:
    water_profile = _get_user_water_profile_or_404(db, water_profile_id=water_profile_id, user_id=current_user.id)

    style_identifier = payload.style_code
    if payload.recipe_id is not None:
        recipe = _get_user_recipe_or_404(db, recipe_id=payload.recipe_id, user_id=current_user.id)
        if not style_identifier:
            style_identifier = recipe.style

    if not style_identifier:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide style_code or recipe_id for recommendation.",
        )

    style = resolve_bjcp_style(style_identifier)
    if style is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BJCP style not found")

    recommendation = build_water_recommendation(
        water_profile=water_profile,
        style=style,
        batch_volume_liters=payload.batch_volume_liters,
    )

    return WaterRecommendationRead(
        water_profile_id=water_profile.id,
        water_profile_name=water_profile.name,
        style_code=style.code,
        style_name=style.name,
        batch_volume_liters=round(payload.batch_volume_liters, 2),
        source_profile=WaterIonSnapshotRead(**recommendation.source_profile.__dict__),
        target_profile=WaterIonSnapshotRead(**recommendation.target_profile.__dict__),
        projected_profile=WaterIonSnapshotRead(**recommendation.projected_profile.__dict__),
        additions=[MineralAdditionRead(**item.__dict__) for item in recommendation.additions],
        notes=list(recommendation.notes),
    )
