"""Zonal statistics computation for village polygons.

Computes mean/median values of raster layers (soil, climate, terrain)
for each village polygon using rasterstats.

Will be implemented in Phase 2.
"""

# TODO (Phase 2): Implement zonal statistics pipeline
# - Load village polygons from PostGIS
# - For each raster layer (soil pH, clay, temperature, rainfall, elevation, slope):
#   - Compute zonal stats (mean/median) per village polygon
# - Output per-village factor values for scoring
#
# Key dependencies: rasterstats, geopandas, rasterio
