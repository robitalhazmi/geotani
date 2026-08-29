"""API router for querying and filtering village crop suitability scores."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import ScoreListResponse, SuitabilityScore, Village, VillageScoreItem
from etl.scoring.crop_params import CROP_REQUIREMENTS

router = APIRouter(prefix="/scores", tags=["Suitability Scores"])


@router.get("", response_model=ScoreListResponse)
def query_scores(
    crop: str = Query(..., description="Crop identifier: 'coffee', 'cocoa', or 'sugarcane'"),
    province: Optional[str] = Query(None, description="Filter by province (e.g. 'Jawa Timur')"),
    kabupaten: Optional[str] = Query(None, description="Filter by regency/city (e.g. 'Malang')"),
    min_score: Optional[float] = Query(
        None, ge=0.0, le=100.0, description="Minimum score threshold"
    ),
    bbox: Optional[str] = Query(
        None,
        description="Bounding box: 'minx,miny,maxx,maxy' in WGS84 (e.g. '112.0,-8.5,113.5,-7.0')",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order: 'desc' or 'asc'"),
    limit: int = Query(100, ge=1, le=1000, description="Max results (default 100, max 1000)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """Query village suitability scores with bounding box and score filters."""
    if crop not in CROP_REQUIREMENTS:
        valid_crops = list(CROP_REQUIREMENTS.keys())
        msg = f"Invalid crop '{crop}'. Valid options: {valid_crops}"
        raise HTTPException(status_code=400, detail=msg)

    query = (
        db.query(
            Village.id,
            Village.adm_pcode,
            Village.name,
            Village.kecamatan,
            Village.kabupaten,
            Village.province,
            Village.resolution,
            SuitabilityScore.crop,
            SuitabilityScore.score,
            SuitabilityScore.climate_score,
            SuitabilityScore.soil_score,
            SuitabilityScore.terrain_score,
            SuitabilityScore.access_score,
        )
        .join(SuitabilityScore, Village.id == SuitabilityScore.village_id)
        .filter(SuitabilityScore.crop == crop)
    )

    if province:
        query = query.filter(func.lower(Village.province) == province.strip().lower())

    if kabupaten:
        query = query.filter(func.lower(Village.kabupaten) == kabupaten.strip().lower())

    if min_score is not None:
        query = query.filter(SuitabilityScore.score >= min_score)

    if bbox:
        try:
            coords = [float(c.strip()) for c in bbox.split(",")]
            if len(coords) != 4:
                raise ValueError
            minx, miny, maxx, maxy = coords
            envelope = func.ST_MakeEnvelope(minx, miny, maxx, maxy, 4326)
            query = query.filter(func.ST_Intersects(Village.geom, envelope))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid bbox format. Expected 'minx,miny,maxx,maxy' with 4 float values.",
            )

    total = query.count()

    if order == "desc":
        query = query.order_by(SuitabilityScore.score.desc(), Village.name.asc())
    else:
        query = query.order_by(SuitabilityScore.score.asc(), Village.name.asc())

    rows = query.offset(offset).limit(limit).all()

    items = [
        VillageScoreItem(
            id=r.id,
            adm_pcode=r.adm_pcode,
            name=r.name,
            kecamatan=r.kecamatan,
            kabupaten=r.kabupaten,
            province=r.province,
            resolution=r.resolution,
            crop=r.crop,
            score=r.score,
            climate_score=r.climate_score,
            soil_score=r.soil_score,
            terrain_score=r.terrain_score,
            access_score=r.access_score,
        )
        for r in rows
    ]

    return ScoreListResponse(
        total=total,
        crop=crop,
        limit=limit,
        offset=offset,
        items=items,
    )
