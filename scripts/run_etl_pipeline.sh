#!/usr/bin/env bash
# ==============================================================================
# GeoTani — End-to-End Production ETL & Scoring Pipeline Execution
# Usage:
#   On VPS (via Docker):
#     sudo docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm api ./scripts/run_etl_pipeline.sh
#   Or locally (in active venv):
#     ./scripts/run_etl_pipeline.sh
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================================================="
echo "        🌾 GeoTani End-to-End Data Pipeline Execution            "
echo "================================================================="

# 1. Download Boundaries
echo ""
echo "▶ [Step 1/5] Downloading Indonesia Administrative Boundaries..."
python -m etl.download.download_boundaries

# 2. Process & Standardize Boundaries
echo ""
echo "▶ [Step 2/5] Standardizing & Filtering Pilot & Nationwide Boundaries..."
python -m etl.boundaries

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
echo "▶ [Step 5/5] Extracting Zonal Stats & Calculating Crop Suitability Scores..."
python -m etl.pipeline --extract

echo ""
echo "================================================================="
echo "  🎉 ETL PIPELINE COMPLETE: PostGIS & Vector Tiles Populated!"
echo "================================================================="
