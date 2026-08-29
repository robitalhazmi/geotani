"""Crop agronomic parameter tables and factor weighting configurations.

Each crop defines optimal and absolute tolerance ranges for key environmental factors.
These parameters drive the fuzzy trapezoidal membership functions in the suitability engine.

Sources:
    - FAO Ecocrop Database
    - Indonesian Ministry of Agriculture (Kementan / Ditjenbun) Technical Guidelines
    - International Cocoa Organization (ICCO) & World Coffee Research (WCR)
    - Indonesian Sugar Research Institute (P3GI)
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class FactorRange:
    """Trapezoidal membership function bounds."""

    min_abs: float  # Value below which score is 0.0
    min_opt: float  # Value at which optimal plateau starts (score = 100.0)
    max_opt: float  # Value at which optimal plateau ends (score = 100.0)
    max_abs: float  # Value above which score is 0.0


@dataclass(frozen=True)
class CropWeights:
    """Weight distribution for composite score calculation."""

    # Soil sub-factors (must sum to 1.0)
    soil_ph: float = 0.40
    clay: float = 0.25
    sand: float = 0.15
    soc: float = 0.20

    # Terrain sub-factors (must sum to 1.0)
    elevation: float = 0.50
    slope: float = 0.50

    # Overall land suitability weights (must sum to 1.0)
    soil: float = 0.40
    terrain: float = 0.35
    access: float = 0.25


@dataclass
class CropRequirement:
    """Comprehensive environmental requirements for a single crop."""

    crop_id: str
    display_name: str
    category: str  # 'perennial' or 'annual'
    annual_mean_temp_c: FactorRange
    annual_rainfall_mm: FactorRange
    elevation_m: FactorRange
    slope_deg: FactorRange
    soil_ph: FactorRange
    clay_pct: FactorRange
    sand_pct: FactorRange
    soc_g_kg: FactorRange
    weights: CropWeights = field(default_factory=CropWeights)


# --- Calibrated Crop Parameter Tables ---

CROP_REQUIREMENTS: Dict[str, CropRequirement] = {
    "coffee": CropRequirement(
        crop_id="coffee",
        display_name="Coffee (Robusta)",
        category="perennial",
        # Optimal 22-26°C, tolerant 18-30°C
        annual_mean_temp_c=FactorRange(min_abs=18.0, min_opt=22.0, max_opt=26.0, max_abs=30.0),
        # Optimal 1500-2500 mm, tolerant 1000-3500 mm
        annual_rainfall_mm=FactorRange(
            min_abs=1000.0, min_opt=1500.0, max_opt=2500.0, max_abs=3500.0
        ),
        # Robusta thrives at 200-800m
        elevation_m=FactorRange(min_abs=0.0, min_opt=200.0, max_opt=800.0, max_abs=1400.0),
        # Gently rolling to moderate hills (0-15° optimal, up to 30° max)
        slope_deg=FactorRange(min_abs=0.0, min_opt=0.0, max_opt=15.0, max_abs=30.0),
        # Slightly acidic soils (5.5 - 6.5 optimal)
        soil_ph=FactorRange(min_abs=4.5, min_opt=5.5, max_opt=6.5, max_abs=7.5),
        # Well-drained loams/clay-loams
        clay_pct=FactorRange(min_abs=10.0, min_opt=20.0, max_opt=45.0, max_abs=65.0),
        sand_pct=FactorRange(min_abs=10.0, min_opt=20.0, max_opt=50.0, max_abs=75.0),
        soc_g_kg=FactorRange(min_abs=5.0, min_opt=15.0, max_opt=60.0, max_abs=100.0),
        weights=CropWeights(
            soil_ph=0.40,
            clay=0.25,
            sand=0.15,
            soc=0.20,
            elevation=0.50,
            slope=0.50,
            soil=0.40,
            terrain=0.35,
            access=0.25,
        ),
    ),
    "cocoa": CropRequirement(
        crop_id="cocoa",
        display_name="Cocoa",
        category="perennial",
        # Warm, humid lowland tropics (22-30°C optimal)
        annual_mean_temp_c=FactorRange(min_abs=18.0, min_opt=22.0, max_opt=30.0, max_abs=34.0),
        # 1500-2500 mm rainfall, sensitive to prolonged dry spells
        annual_rainfall_mm=FactorRange(
            min_abs=1200.0, min_opt=1500.0, max_opt=2500.0, max_abs=3200.0
        ),
        # Lowlands below 500m (up to 800m max)
        elevation_m=FactorRange(min_abs=0.0, min_opt=50.0, max_opt=500.0, max_abs=900.0),
        # Gentle slopes to prevent erosion and retain moisture
        slope_deg=FactorRange(min_abs=0.0, min_opt=0.0, max_opt=10.0, max_abs=25.0),
        # Near neutral pH (6.0 - 7.2 optimal)
        soil_ph=FactorRange(min_abs=5.0, min_opt=6.0, max_opt=7.2, max_abs=8.0),
        # Deep, organic-rich clay loam
        clay_pct=FactorRange(min_abs=15.0, min_opt=25.0, max_opt=45.0, max_abs=60.0),
        sand_pct=FactorRange(min_abs=10.0, min_opt=20.0, max_opt=45.0, max_abs=70.0),
        soc_g_kg=FactorRange(min_abs=10.0, min_opt=20.0, max_opt=70.0, max_abs=100.0),
        weights=CropWeights(
            soil_ph=0.40,
            clay=0.25,
            sand=0.15,
            soc=0.20,
            elevation=0.45,
            slope=0.55,
            soil=0.45,
            terrain=0.30,
            access=0.25,
        ),
    ),
    "sugarcane": CropRequirement(
        crop_id="sugarcane",
        display_name="Sugarcane",
        category="annual",
        # Warm with strong sunshine (24-30°C optimal)
        annual_mean_temp_c=FactorRange(min_abs=18.0, min_opt=24.0, max_opt=30.0, max_abs=36.0),
        # 1500-2500 mm rainfall, benefits from dry ripening period
        annual_rainfall_mm=FactorRange(
            min_abs=1000.0, min_opt=1500.0, max_opt=2500.0, max_abs=3000.0
        ),
        # Flat alluvial plains, 0-400m
        elevation_m=FactorRange(min_abs=0.0, min_opt=0.0, max_opt=400.0, max_abs=900.0),
        # Flat to very gentle slopes (0-6° optimal for mechanization and irrigation)
        slope_deg=FactorRange(min_abs=0.0, min_opt=0.0, max_opt=6.0, max_abs=15.0),
        # 6.0 - 7.5 pH
        soil_ph=FactorRange(min_abs=5.0, min_opt=6.0, max_opt=7.5, max_abs=8.5),
        # Fertile alluvial/volcanic soils
        clay_pct=FactorRange(min_abs=10.0, min_opt=20.0, max_opt=40.0, max_abs=55.0),
        sand_pct=FactorRange(min_abs=15.0, min_opt=25.0, max_opt=55.0, max_abs=80.0),
        soc_g_kg=FactorRange(min_abs=5.0, min_opt=15.0, max_opt=50.0, max_abs=80.0),
        weights=CropWeights(
            soil_ph=0.35,
            clay=0.25,
            sand=0.20,
            soc=0.20,
            elevation=0.40,
            slope=0.60,
            soil=0.35,
            terrain=0.40,
            access=0.25,
        ),
    ),
}
