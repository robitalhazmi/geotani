"""SQLAlchemy / GeoAlchemy2 models for TaniScope."""

# Models will be implemented in Phase 3 when the database schema is finalized.
# See docs/03_IMPLEMENTATION_PLAN.md §7 for the planned schema.
#
# Planned tables:
#   - villages: geometry + admin metadata (adm4_pcode, name, kecamatan, kabupaten, province)
#   - suitability_scores: village_id, crop, score, factor breakdown, computed_at
