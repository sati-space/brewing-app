from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ingredient_profile import IngredientProfile
from app.models.user import User
from app.schemas.ingredients import IngredientProfileCreate, IngredientProfileRead, IngredientProfileUpdate

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


def _get_user_ingredient_or_404(db: Session, ingredient_id: int, user_id: int) -> IngredientProfile:
    ingredient = (
        db.query(IngredientProfile)
        .filter(
            IngredientProfile.id == ingredient_id,
            IngredientProfile.owner_user_id == user_id,
        )
        .first()
    )
    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient profile not found")
    return ingredient


@router.post("", response_model=IngredientProfileRead, status_code=status.HTTP_201_CREATED)
def create_ingredient_profile(
    payload: IngredientProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IngredientProfile:
    existing = (
        db.query(IngredientProfile)
        .filter(
            IngredientProfile.owner_user_id == current_user.id,
            IngredientProfile.name == payload.name,
            IngredientProfile.ingredient_type == payload.ingredient_type,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient profile already exists")

    ingredient = IngredientProfile(
        owner_user_id=current_user.id,
        name=payload.name,
        ingredient_type=payload.ingredient_type,
        default_unit=payload.default_unit,
        notes=payload.notes,
    )

    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.get("", response_model=list[IngredientProfileRead])
def list_ingredient_profiles(
    ingredient_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IngredientProfile]:
    query = db.query(IngredientProfile).filter(IngredientProfile.owner_user_id == current_user.id)

    if ingredient_type:
        query = query.filter(IngredientProfile.ingredient_type == ingredient_type)

    if search:
        like_term = f"%{search}%"
        query = query.filter(IngredientProfile.name.ilike(like_term))

    return query.order_by(IngredientProfile.ingredient_type.asc(), IngredientProfile.name.asc()).all()


@router.get("/{ingredient_id}", response_model=IngredientProfileRead)
def get_ingredient_profile(
    ingredient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IngredientProfile:
    return _get_user_ingredient_or_404(db, ingredient_id=ingredient_id, user_id=current_user.id)


@router.put("/{ingredient_id}", response_model=IngredientProfileRead)
def update_ingredient_profile(
    ingredient_id: int,
    payload: IngredientProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IngredientProfile:
    ingredient = _get_user_ingredient_or_404(db, ingredient_id=ingredient_id, user_id=current_user.id)

    duplicate = (
        db.query(IngredientProfile)
        .filter(
            IngredientProfile.owner_user_id == current_user.id,
            IngredientProfile.name == payload.name,
            IngredientProfile.ingredient_type == payload.ingredient_type,
            IngredientProfile.id != ingredient.id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient profile already exists")

    ingredient.name = payload.name
    ingredient.ingredient_type = payload.ingredient_type
    ingredient.default_unit = payload.default_unit
    ingredient.notes = payload.notes

    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient_profile(
    ingredient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ingredient = _get_user_ingredient_or_404(db, ingredient_id=ingredient_id, user_id=current_user.id)

    db.delete(ingredient)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
