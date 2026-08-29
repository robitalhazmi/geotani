"""API router for crop catalogue and parameter metadata."""

from typing import List

from fastapi import APIRouter, HTTPException

from api.models import CropInfo, FactorRangeInfo
from etl.scoring.crop_params import CROP_REQUIREMENTS

router = APIRouter(prefix="/crops", tags=["Crops"])


def format_crop_info(crop_id: str) -> CropInfo:
    req = CROP_REQUIREMENTS[crop_id]
    t_opt = f"{req.annual_mean_temp_c.min_opt:.1f} - {req.annual_mean_temp_c.max_opt:.1f} °C"
    r_opt = f"{req.annual_rainfall_mm.min_opt:.0f} - {req.annual_rainfall_mm.max_opt:.0f} mm"
    e_opt = f"{req.elevation_m.min_opt:.0f} - {req.elevation_m.max_opt:.0f} m"
    p_opt = f"{req.soil_ph.min_opt:.1f} - {req.soil_ph.max_opt:.1f}"
    s_opt = f"{req.slope_deg.min_opt:.1f} - {req.slope_deg.max_opt:.1f}°"

    return CropInfo(
        crop_id=req.crop_id,
        display_name=req.display_name,
        category=req.category,
        optimal_temperature_c=t_opt,
        optimal_rainfall_mm=r_opt,
        optimal_elevation_m=e_opt,
        optimal_ph=p_opt,
        optimal_slope_deg=s_opt,
        factors={
            "temperature": FactorRangeInfo(
                min_abs=req.annual_mean_temp_c.min_abs,
                min_opt=req.annual_mean_temp_c.min_opt,
                max_opt=req.annual_mean_temp_c.max_opt,
                max_abs=req.annual_mean_temp_c.max_abs,
            ),
            "rainfall": FactorRangeInfo(
                min_abs=req.annual_rainfall_mm.min_abs,
                min_opt=req.annual_rainfall_mm.min_opt,
                max_opt=req.annual_rainfall_mm.max_opt,
                max_abs=req.annual_rainfall_mm.max_abs,
            ),
            "elevation": FactorRangeInfo(
                min_abs=req.elevation_m.min_abs,
                min_opt=req.elevation_m.min_opt,
                max_opt=req.elevation_m.max_opt,
                max_abs=req.elevation_m.max_abs,
            ),
            "slope": FactorRangeInfo(
                min_abs=req.slope_deg.min_abs,
                min_opt=req.slope_deg.min_opt,
                max_opt=req.slope_deg.max_opt,
                max_abs=req.slope_deg.max_abs,
            ),
            "soil_ph": FactorRangeInfo(
                min_abs=req.soil_ph.min_abs,
                min_opt=req.soil_ph.min_opt,
                max_opt=req.soil_ph.max_opt,
                max_abs=req.soil_ph.max_abs,
            ),
            "clay": FactorRangeInfo(
                min_abs=req.clay_pct.min_abs,
                min_opt=req.clay_pct.min_opt,
                max_opt=req.clay_pct.max_opt,
                max_abs=req.clay_pct.max_abs,
            ),
            "sand": FactorRangeInfo(
                min_abs=req.sand_pct.min_abs,
                min_opt=req.sand_pct.min_opt,
                max_opt=req.sand_pct.max_opt,
                max_abs=req.sand_pct.max_abs,
            ),
            "soc": FactorRangeInfo(
                min_abs=req.soc_g_kg.min_abs,
                min_opt=req.soc_g_kg.min_opt,
                max_opt=req.soc_g_kg.max_opt,
                max_abs=req.soc_g_kg.max_abs,
            ),
        },
        weights={
            "soil": req.weights.soil,
            "terrain": req.weights.terrain,
            "access": req.weights.access,
            "soil_ph": req.weights.soil_ph,
            "clay": req.weights.clay,
            "sand": req.weights.sand,
            "soc": req.weights.soc,
            "elevation": req.weights.elevation,
            "slope": req.weights.slope,
        },
    )


@router.get("", response_model=List[CropInfo])
def list_crops():
    """List all supported crops with agronomic parameters and optimal ranges."""
    return [format_crop_info(crop_id) for crop_id in CROP_REQUIREMENTS.keys()]


@router.get("/{crop_id}", response_model=CropInfo)
def get_crop(crop_id: str):
    """Get detailed agronomic parameters and weights for a specific crop."""
    if crop_id not in CROP_REQUIREMENTS:
        raise HTTPException(status_code=404, detail=f"Crop '{crop_id}' not found.")
    return format_crop_info(crop_id)
