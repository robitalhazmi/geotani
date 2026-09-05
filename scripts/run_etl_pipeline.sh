#!/usr/bin/env bash
# ==============================================================================
# GeoTani — End-to-End Production ETL & Scoring Pipeline Execution (Resumable)
#
# Usage:
#   On VPS (via Docker):
#     sudo docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm api ./scripts/run_etl_pipeline.sh
#   To force re-computing everything from scratch:
#     sudo docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm api ./scripts/run_etl_pipeline.sh --force
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

FORCE_FLAG=""
if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
    FORCE_FLAG="--force"
    echo "⚠️  Force mode enabled: All intermediate files will be re-processed."
fi

echo "================================================================="
echo "   🌾 GeoTani End-to-End Data Pipeline Execution (Resumable)     "
echo "================================================================="

# 1. Download Boundaries
echo ""
echo "▶ [Step 1/5] Downloading Indonesia Administrative Boundaries..."
python -m etl.download.download_boundaries

# 2. Process & Standardize Boundaries
echo ""
echo "▶ [Step 2/5] Standardizing & Filtering Pilot & Nationwide Boundaries..."
if [ -n "$FORCE_FLAG" ]; then
    python -m etl.boundaries --force
else
    python -m etl.boundaries
fi

# 3. Download Environmental Data
echo ""
echo "▶ [Step 3/5] Downloading Environmental Datasets (Climate, Soil, Terrain, OSM)..."
python -m etl.download.download_worldclim || true
python -m etl.download.download_soilgrids || true
python -m etl.download.download_srtm || true
python -m etl.download.download_osm || true

# 4. Ingest Base Boundaries to PostGIS
echo ""
echo "▶ [Step 4/5] Initializing PostGIS Schema & Ingesting Boundaries..."
python -m etl.load_postgis

# 5. Extract Zonal Statistics & Calculate Suitability Scores
echo ""
echo "▶ [Step 5/5] Calculating Crop Suitability Scores & Ingesting to PostGIS..."
if [ -n "$FORCE_FLAG" ]; then
    python -m etl.pipeline --extract
else
    python -m etl.pipeline
fi

echo ""
echo "================================================================="
echo "  🎉 ETL PIPELINE COMPLETE: PostGIS & Vector Tiles Populated!"
echo "================================================================="
echo "  💡 Note: On production VPS, remember to restart the tile server:"
echo "     sudo docker compose --env-file .env.prod -f docker-compose.prod.yml restart tiles"
echo "================================================================="

