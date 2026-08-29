"""Unit tests for fuzzy suitability scoring engine and crop parameter calculations."""

import numpy as np
import pytest

from etl.scoring.crop_params import CROP_REQUIREMENTS, FactorRange
from etl.scoring.fuzzy import (
    compute_access_score,
    score_village_factors,
    trapezoidal_score,
)


def test_trapezoidal_score_plateau():
    """Values in the optimal range should score 100.0."""
    bounds = FactorRange(min_abs=10.0, min_opt=20.0, max_opt=30.0, max_abs=40.0)
    assert trapezoidal_score(20.0, bounds) == 100.0
    assert trapezoidal_score(25.0, bounds) == 100.0
    assert trapezoidal_score(30.0, bounds) == 100.0


def test_trapezoidal_score_outside_bounds():
    """Values below min_abs or above max_abs should score 0.0."""
    bounds = FactorRange(min_abs=10.0, min_opt=20.0, max_opt=30.0, max_abs=40.0)
    assert trapezoidal_score(5.0, bounds) == 0.0
    assert trapezoidal_score(10.0, bounds) == 0.0
    assert trapezoidal_score(40.0, bounds) == 0.0
    assert trapezoidal_score(50.0, bounds) == 0.0


def test_trapezoidal_score_ramps():
    """Values on the ramping slopes should interpolate linearly between 0 and 100."""
    bounds = FactorRange(min_abs=10.0, min_opt=20.0, max_opt=30.0, max_abs=40.0)
    # Midpoint of left ramp: (10 + 20) / 2 = 15 -> 50%
    assert trapezoidal_score(15.0, bounds) == pytest.approx(50.0)
    # Midpoint of right ramp: (30 + 40) / 2 = 35 -> 50%
    assert trapezoidal_score(35.0, bounds) == pytest.approx(50.0)


def test_trapezoidal_score_vectorized():
    """Vectorized numpy inputs should return matching array scores."""
    bounds = FactorRange(min_abs=10.0, min_opt=20.0, max_opt=30.0, max_abs=40.0)
    arr = np.array([5.0, 15.0, 25.0, 35.0, 45.0, np.nan])
    scores = trapezoidal_score(arr, bounds)
    assert np.allclose(scores[:5], [0.0, 50.0, 100.0, 50.0, 0.0])
    assert scores[5] == 0.0


def test_access_score_decay():
    """Road distance decay function tests."""
    assert compute_access_score(0.0) == 100.0
    assert compute_access_score(25000.0) == pytest.approx(50.0)
    assert compute_access_score(50000.0) == 0.0
    assert compute_access_score(100000.0) == 0.0


def test_climate_gate_limiting_behavior():
    """Hostile climate condition should zero out score despite perfect soil."""
    coffee = CROP_REQUIREMENTS["coffee"]
    hostile_climate_factors = {
        "temp_c": 10.0,  # Below Robusta minimum (18°C) -> score = 0
        "rainfall_mm": 2000.0,  # Optimal rainfall
        "elevation_m": 500.0,  # Optimal elevation
        "slope_deg": 5.0,  # Optimal slope
        "soil_ph": 6.0,  # Perfect pH
        "clay_pct": 30.0,  # Perfect texture
        "sand_pct": 30.0,
        "soc_g_kg": 30.0,
        "dist_road_m": 100.0,
    }
    result = score_village_factors(hostile_climate_factors, coffee)
    assert result["climate_score"] == 0.0
    assert result["final_score"] == 0.0
    assert result["soil_score"] > 80.0  # Soil was excellent but gated to 0


def test_ideal_conditions_high_score():
    """Under ideal conditions, the final score should approach 100%."""
    sugarcane = CROP_REQUIREMENTS["sugarcane"]
    ideal_factors = {
        "temp_c": 27.0,  # Optimal (24-30)
        "rainfall_mm": 2000.0,  # Optimal (1500-2500)
        "elevation_m": 50.0,  # Optimal lowland
        "slope_deg": 2.0,  # Optimal flat
        "soil_ph": 6.8,  # Optimal (6.0-7.5)
        "clay_pct": 30.0,  # Optimal (20-40)
        "sand_pct": 35.0,  # Optimal (25-55)
        "soc_g_kg": 30.0,  # Optimal (15-50)
        "dist_road_m": 500.0,  # Near road (~99%)
    }
    result = score_village_factors(ideal_factors, sugarcane)
    assert result["final_score"] >= 95.0
    assert result["climate_score"] == 100.0
    assert result["soil_score"] == 100.0
    assert result["terrain_score"] == 100.0


def test_all_pilot_crops_present():
    """Verify all 3 pilot crops are properly configured."""
    assert "coffee" in CROP_REQUIREMENTS
    assert "cocoa" in CROP_REQUIREMENTS
    assert "sugarcane" in CROP_REQUIREMENTS
