"""Database ORM models and Pydantic schemas for TaniScope API."""

from datetime import datetime
from typing import Dict, List, Optional

from geoalchemy2 import Geometry
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from api.database import Base

# --- SQLAlchemy ORM Models ---


class Village(Base):
    """Administrative village or dissolved region boundary polygon."""

    __tablename__ = "villages"

    id = Column(Integer, primary_key=True, index=True)
    adm_pcode = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    kecamatan = Column(String, nullable=True)
    kabupaten = Column(String, nullable=True, index=True)
    province = Column(String, nullable=True, index=True)
    resolution = Column(String, nullable=False, index=True)  # 'village' or 'coarse'
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)

    scores = relationship(
        "SuitabilityScore",
        back_populates="village",
        cascade="all, delete-orphan",
    )


class SuitabilityScore(Base):
    """Calculated agricultural suitability score per village and crop."""

    __tablename__ = "suitability_scores"

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(
        Integer,
        ForeignKey("villages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crop = Column(String, nullable=False, index=True)
    score = Column(Float, nullable=False, index=True)
    climate_score = Column(Float, nullable=True)
    soil_score = Column(Float, nullable=True)
    terrain_score = Column(Float, nullable=True)
    access_score = Column(Float, nullable=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    village = relationship("Village", back_populates="scores")


# --- Pydantic v2 Response Schemas ---


class CropScoreDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crop: str
    score: float
    climate_score: Optional[float] = None
    soil_score: Optional[float] = None
    terrain_score: Optional[float] = None
    access_score: Optional[float] = None
    computed_at: Optional[datetime] = None


class VillageDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    adm_pcode: str
    name: str
    kecamatan: Optional[str] = None
    kabupaten: Optional[str] = None
    province: Optional[str] = None
    resolution: str
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    bbox: Optional[List[float]] = None  # [minx, miny, maxx, maxy]
    scores: List[CropScoreDetail] = []


class VillageScoreItem(BaseModel):
    id: int
    adm_pcode: str
    name: str
    kecamatan: Optional[str] = None
    kabupaten: Optional[str] = None
    province: Optional[str] = None
    resolution: str
    crop: str
    score: float
    climate_score: Optional[float] = None
    soil_score: Optional[float] = None
    terrain_score: Optional[float] = None
    access_score: Optional[float] = None


class ScoreListResponse(BaseModel):
    total: int
    crop: str
    limit: int
    offset: int
    items: List[VillageScoreItem]


class FactorRangeInfo(BaseModel):
    min_abs: float
    min_opt: float
    max_opt: float
    max_abs: float


class CropInfo(BaseModel):
    crop_id: str
    display_name: str
    category: str
    optimal_temperature_c: str
    optimal_rainfall_mm: str
    optimal_elevation_m: str
    optimal_ph: str
    optimal_slope_deg: str
    factors: Dict[str, FactorRangeInfo]
    weights: Dict[str, float]


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    total_villages: int
    total_scores: int
