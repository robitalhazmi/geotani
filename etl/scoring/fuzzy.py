"""Fuzzy logic scoring engine using trapezoidal membership functions.

Implements FAO-style land evaluation with a Climate Gate mechanism:
    FinalScore = ClimateGate * (w_soil*SoilScore + w_terrain*TerrainScore + w_access*AccessScore)
"""

from typing import Any, Dict, Union

import numpy as np

from etl.scoring.crop_params import CropRequirement, FactorRange


def trapezoidal_score(
    value: Union[float, int, np.ndarray],
    bounds: FactorRange,
) -> Union[float, np.ndarray]:
    """Calculate 0-100% suitability score using a trapezoidal membership curve."""
    is_scalar = np.isscalar(value)
    val = np.atleast_1d(np.asarray(value, dtype=np.float64))

    score = np.zeros_like(val, dtype=np.float64)

    # Optimal range [min_opt, max_opt] -> 100.0
    opt_mask = (val >= bounds.min_opt) & (val <= bounds.max_opt)
    score[opt_mask] = 100.0

    # Left ramp [min_abs, min_opt) -> linear increase 0 to 100
    if bounds.min_opt > bounds.min_abs:
        left_mask = (val > bounds.min_abs) & (val < bounds.min_opt)
        score[left_mask] = (
            100.0 * (val[left_mask] - bounds.min_abs) / (bounds.min_opt - bounds.min_abs)
        )

    # Right ramp (max_opt, max_abs] -> linear decrease 100 to 0
    if bounds.max_abs > bounds.max_opt:
        right_mask = (val > bounds.max_opt) & (val < bounds.max_abs)
        score[right_mask] = (
            100.0 * (bounds.max_abs - val[right_mask]) / (bounds.max_abs - bounds.max_opt)
        )

    score[np.isnan(val)] = 0.0
    score = np.clip(score, 0.0, 100.0)

    return float(score[0]) if is_scalar else score


def compute_access_score(
    distance_meters: Union[float, int, np.ndarray],
    max_distance_meters: float = 50000.0,  # 50 km cutoff
) -> Union[float, np.ndarray]:
    """Calculate accessibility score based on distance to nearest road network."""
    is_scalar = np.isscalar(distance_meters)
    dist = np.atleast_1d(np.asarray(distance_meters, dtype=np.float64))

    score = np.clip(100.0 * (1.0 - (dist / max_distance_meters)), 0.0, 100.0)
    score[np.isnan(dist)] = 50.0  # Default neutral score if road data is missing

    return float(score[0]) if is_scalar else score


def score_village_factors(
    factors: Dict[str, float],
    crop: CropRequirement,
) -> Dict[str, Any]:
    """Compute the multi-tier suitability score for a single village dictionary."""
    w = crop.weights

    # 1. Individual factor scores
    s_temp = trapezoidal_score(factors.get("temp_c", np.nan), crop.annual_mean_temp_c)
    s_rain = trapezoidal_score(factors.get("rainfall_mm", np.nan), crop.annual_rainfall_mm)
    s_elev = trapezoidal_score(factors.get("elevation_m", np.nan), crop.elevation_m)
    s_slope = trapezoidal_score(factors.get("slope_deg", np.nan), crop.slope_deg)
    s_ph = trapezoidal_score(factors.get("soil_ph", np.nan), crop.soil_ph)
    s_clay = trapezoidal_score(factors.get("clay_pct", np.nan), crop.clay_pct)
    s_sand = trapezoidal_score(factors.get("sand_pct", np.nan), crop.sand_pct)
    s_soc = trapezoidal_score(factors.get("soc_g_kg", np.nan), crop.soc_g_kg)

    dist_road = factors.get("dist_road_m", 5000.0)
    s_access = compute_access_score(dist_road)

    # 2. Climate Gate (limiting factor)
    climate_score = min(s_temp, s_rain)
    climate_gate = climate_score / 100.0

    # 3. Composite Sub-scores
    soil_score = w.soil_ph * s_ph + w.clay * s_clay + w.sand * s_sand + w.soc * s_soc
    terrain_score = w.elevation * s_elev + w.slope * s_slope

    # 4. Overall Land Score (weighted average of soil, terrain, access)
    land_score = w.soil * soil_score + w.terrain * terrain_score + w.access * s_access

    # 5. Final Gated Score
    final_score = round(float(climate_gate * land_score), 2)

    return {
        "crop": crop.crop_id,
        "crop_name": crop.display_name,
        "final_score": final_score,
        "climate_score": round(float(climate_score), 2),
        "soil_score": round(float(soil_score), 2),
        "terrain_score": round(float(terrain_score), 2),
        "access_score": round(float(s_access), 2),
        "factor_scores": {
            "temp": round(float(s_temp), 2),
            "rainfall": round(float(s_rain), 2),
            "elevation": round(float(s_elev), 2),
            "slope": round(float(s_slope), 2),
            "soil_ph": round(float(s_ph), 2),
            "clay": round(float(s_clay), 2),
            "sand": round(float(s_sand), 2),
            "soc": round(float(s_soc), 2),
            "access": round(float(s_access), 2),
        },
    }
