"""ETL pipeline orchestrator for TaniScope.

Orchestrates the full data processing pipeline:
1. Load/validate village boundaries
2. Compute zonal statistics for each raster layer
3. Run suitability scoring for each crop
4. Write results to PostGIS

Will be implemented in Phase 2.
"""

# TODO (Phase 2): Implement the full ETL pipeline
# - Read raw raster data from data/raw/
# - Compute zonal stats per village (see zonal_stats.py)
# - Score each village × crop using scoring/crop_params.py
# - Load results into PostGIS suitability_scores table
#
# See docs/03_IMPLEMENTATION_PLAN.md §4 for scoring methodology
