"""API router for village detail, administrative hierarchy, and crop breakdowns."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import CropScoreDetail, Village, VillageDetail

router = APIRouter(prefix="/villages", tags=["Villages"])


def build_village_detail_response(village: Village, db: Session) -> VillageDetail:
    """Helper to compute centroid and bounding box from PostGIS geometry."""
    spatial_data = (
        db.query(
            func.ST_Y(func.ST_Centroid(village.geom)).label("lat"),
            func.ST_X(func.ST_Centroid(village.geom)).label("lon"),
            func.ST_XMin(village.geom).label("minx"),
            func.ST_YMin(village.geom).label("miny"),
            func.ST_XMax(village.geom).label("maxx"),
            func.ST_YMax(village.geom).label("maxy"),
        )
        .filter(Village.id == village.id)
        .first()
    )

    scores_list = [
        CropScoreDetail(
            crop=s.crop,
            score=s.score,
            climate_score=s.climate_score,
            soil_score=s.soil_score,
            terrain_score=s.terrain_score,
            access_score=s.access_score,
            computed_at=s.computed_at,
        )
        for s in village.scores
    ]

    return VillageDetail(
        id=village.id,
        adm_pcode=village.adm_pcode,
        name=village.name,
        kecamatan=village.kecamatan,
        kabupaten=village.kabupaten,
        province=village.province,
        resolution=village.resolution,
        center_lat=round(spatial_data.lat, 5) if spatial_data else None,
        center_lon=round(spatial_data.lon, 5) if spatial_data else None,
        bbox=(
            [
                round(spatial_data.minx, 5),
                round(spatial_data.miny, 5),
                round(spatial_data.maxx, 5),
                round(spatial_data.maxy, 5),
            ]
            if spatial_data
            else None
        ),
        scores=scores_list,
    )


@router.get("/search", response_model=list[VillageDetail])
def search_villages(
    q: str,
    limit: int = 8,
    db: Session = Depends(get_db),
):
    """Search villages by name, kecamatan, kabupaten, or administrative P-code."""
    search_pattern = f"%{q.strip().lower()}%"
    villages = (
        db.query(Village)
        .filter(
            func.lower(Village.name).like(search_pattern)
            | func.lower(Village.adm_pcode).like(search_pattern)
            | func.lower(Village.kecamatan).like(search_pattern)
            | func.lower(Village.kabupaten).like(search_pattern)
        )
        .limit(limit)
        .all()
    )
    return [build_village_detail_response(v, db) for v in villages]


@router.get("/{village_id}", response_model=VillageDetail)
def get_village_by_id(village_id: int, db: Session = Depends(get_db)):
    """Retrieve full village metadata, geographic center, and all crop scores."""
    village = db.query(Village).filter(Village.id == village_id).first()
    if not village:
        raise HTTPException(status_code=404, detail=f"Village with ID {village_id} not found.")

    return build_village_detail_response(village, db)


@router.get("/by-pcode/{adm_pcode}", response_model=VillageDetail)
def get_village_by_pcode(adm_pcode: str, db: Session = Depends(get_db)):
    """Retrieve full village metadata by BPS administrative P-code."""
    village = db.query(Village).filter(Village.adm_pcode == adm_pcode).first()
    if not village:
        raise HTTPException(status_code=404, detail=f"Village '{adm_pcode}' not found.")

    return build_village_detail_response(village, db)
