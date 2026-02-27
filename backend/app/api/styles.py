from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.styles import BJCPStyleListResponse, BJCPStyleRead, IonRangeRead
from app.services.bjcp_styles import BJCPStyleProfile, list_bjcp_styles, resolve_bjcp_style

router = APIRouter(prefix="/styles", tags=["styles"])


def _to_style_read(style: BJCPStyleProfile) -> BJCPStyleRead:
    return BJCPStyleRead(
        code=style.code,
        name=style.name,
        category=style.category,
        impression=style.impression,
        examples=list(style.examples),
        calcium_ppm=IonRangeRead(
            min_ppm=style.calcium_ppm.min_ppm,
            max_ppm=style.calcium_ppm.max_ppm,
            target_ppm=style.calcium_ppm.target_ppm,
        ),
        magnesium_ppm=IonRangeRead(
            min_ppm=style.magnesium_ppm.min_ppm,
            max_ppm=style.magnesium_ppm.max_ppm,
            target_ppm=style.magnesium_ppm.target_ppm,
        ),
        sodium_ppm=IonRangeRead(
            min_ppm=style.sodium_ppm.min_ppm,
            max_ppm=style.sodium_ppm.max_ppm,
            target_ppm=style.sodium_ppm.target_ppm,
        ),
        chloride_ppm=IonRangeRead(
            min_ppm=style.chloride_ppm.min_ppm,
            max_ppm=style.chloride_ppm.max_ppm,
            target_ppm=style.chloride_ppm.target_ppm,
        ),
        sulfate_ppm=IonRangeRead(
            min_ppm=style.sulfate_ppm.min_ppm,
            max_ppm=style.sulfate_ppm.max_ppm,
            target_ppm=style.sulfate_ppm.target_ppm,
        ),
        bicarbonate_ppm=IonRangeRead(
            min_ppm=style.bicarbonate_ppm.min_ppm,
            max_ppm=style.bicarbonate_ppm.max_ppm,
            target_ppm=style.bicarbonate_ppm.target_ppm,
        ),
    )


@router.get("/bjcp", response_model=BJCPStyleListResponse)
def get_bjcp_styles(
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
) -> BJCPStyleListResponse:
    del current_user
    styles = [_to_style_read(style) for style in list_bjcp_styles(search=search)]
    return BJCPStyleListResponse(count=len(styles), items=styles)


@router.get("/bjcp/{style_identifier}", response_model=BJCPStyleRead)
def get_bjcp_style(
    style_identifier: str,
    current_user: User = Depends(get_current_user),
) -> BJCPStyleRead:
    del current_user
    style = resolve_bjcp_style(style_identifier)
    if style is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BJCP style not found")
    return _to_style_read(style)
