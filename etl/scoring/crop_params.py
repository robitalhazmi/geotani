"""Crop agronomic parameter tables for suitability scoring.

Each crop defines optimal and absolute tolerance ranges for key factors.
These are used by the fuzzy trapezoidal membership function to compute
per-factor suitability scores (0-100).

Sources:
    - FAO Ecocrop database
    - Plantation crop agronomy literature
    - See docs/03_IMPLEMENTATION_PLAN.md §4 for methodology details

Parameter format per factor:
    (min_absolute, min_optimal, max_optimal, max_absolute)
    - Below min_absolute or above max_absolute: score = 0
    - Between min_optimal and max_optimal: score = 100
    - Ramping zones: linear interpolation
"""

from typing import TypedDict


class FactorRange(TypedDict):
    """Trapezoidal membership function parameters."""
    min_abs: float   # Below this → score = 0
    min_opt: float   # Start of optimal range (score = 100)
    max_opt: float   # End of optimal range (score = 100)
    max_abs: float   # Above this → score = 0


class CropParams(TypedDict):
    """Full parameter set for one crop."""
    name: str
    annual_rainfall_mm: FactorRange
    annual_mean_temp_c: FactorRange
    elevation_m: FactorRange
    soil_ph: FactorRange
    slope_pct: FactorRange


# --- Crop parameter tables (to be refined during Phase 2 calibration) ---

CROP_PARAMS: dict[str, CropParams] = {
    "coffee_robusta": {
        "name": "Coffee (Robusta)",
        "annual_rainfall_mm": {"min_abs": 1000, "min_opt": 1500, "max_opt": 3000, "max_abs": 4000},
        "annual_mean_temp_c": {"min_abs": 18, "min_opt": 21, "max_opt": 24, "max_abs": 30},
        "elevation_m":        {"min_abs": 0, "min_opt": 100, "max_opt": 800, "max_abs": 1500},
        "soil_ph":            {"min_abs": 4.5, "min_opt": 5.5, "max_opt": 6.5, "max_abs": 7.5},
        "slope_pct":          {"min_abs": 0, "min_opt": 0, "max_opt": 15, "max_abs": 35},
    },
    "cocoa": {
        "name": "Cocoa",
        "annual_rainfall_mm": {"min_abs": 1000, "min_opt": 1500, "max_opt": 2500, "max_abs": 3500},
        "annual_mean_temp_c": {"min_abs": 18, "min_opt": 21, "max_opt": 32, "max_abs": 35},
        "elevation_m":        {"min_abs": 0, "min_opt": 0, "max_opt": 600, "max_abs": 1000},
        "soil_ph":            {"min_abs": 5.0, "min_opt": 6.0, "max_opt": 7.5, "max_abs": 8.0},
        "slope_pct":          {"min_abs": 0, "min_opt": 0, "max_opt": 12, "max_abs": 25},
    },
    "sugarcane": {
        "name": "Sugarcane",
        "annual_rainfall_mm": {"min_abs": 800, "min_opt": 1500, "max_opt": 2500, "max_abs": 3500},
        "annual_mean_temp_c": {"min_abs": 20, "min_opt": 24, "max_opt": 30, "max_abs": 38},
        "elevation_m":        {"min_abs": 0, "min_opt": 0, "max_opt": 800, "max_abs": 1500},
        "soil_ph":            {"min_abs": 5.0, "min_opt": 6.0, "max_opt": 7.5, "max_abs": 8.5},
        "slope_pct":          {"min_abs": 0, "min_opt": 0, "max_opt": 8, "max_abs": 16},
    },
}
