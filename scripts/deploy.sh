#!/usr/bin/env bash
# ==============================================================================
# GeoTani — Production Deployment Script for VPS
# Usage: ./scripts/deploy.sh
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================================================="
echo "               🌾 GeoTani Production Deployment                 "
echo "================================================================="

# 1. Check prerequisites
echo "1. Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose v2 is not installed."
    exit 1
fi
echo "   ✓ Docker & Docker Compose are available."

# 2. Check environment file
ENV_FILE=".env.prod"
if [ ! -f "$ENV_FILE" ]; then
    echo "2. No .env.prod found. Generating from .env.prod.example..."
    if [ -f ".env.prod.example" ]; then
        cp .env.prod.example "$ENV_FILE"
        # Generate random password
        RAND_PASS=$(openssl rand -hex 16 2>/dev/null || tr -dc A-Za-z0-9 </dev/urandom | head -c 24)
        sed -i "s/CHANGE_THIS_TO_A_SECURE_RANDOM_PASSWORD_IN_PRODUCTION/$RAND_PASS/" "$ENV_FILE"
        echo "   ✓ Created $ENV_FILE with auto-generated secure password."
    else
        echo "❌ Error: .env.prod.example not found."
        exit 1
    fi
else
    echo "2. Found existing $ENV_FILE."
fi

# Load variables
source "$ENV_FILE"
echo "   Target Domain: ${DOMAIN_NAME:-geotani.cloud}"

# 3. Build and launch production stack
echo ""
echo "3. Building and launching production containers..."
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml up -d --build

# 4. Wait for database health
echo ""
echo "4. Waiting for PostGIS database to be healthy..."
RETRIES=30
until [ $RETRIES -le 0 ] || docker inspect --format='{{.State.Health.Status}}' geotani-prod-db 2>/dev/null | grep -q "healthy"; do
    echo "   Waiting for database... ($RETRIES attempts remaining)"
    sleep 2
    RETRIES=$((RETRIES - 1))
done

if [ $RETRIES -le 0 ]; then
    echo "❌ Database failed to become healthy. Check logs with: docker compose -f docker-compose.prod.yml logs db"
    exit 1
fi
echo "   ✓ PostGIS database is ready and healthy."

# 5. Check if database is populated
echo ""
echo "5. Verifying database records..."
RECORD_COUNT=$(docker exec geotani-prod-db psql -U "${POSTGRES_USER:-geotani}" -d "${POSTGRES_DB:-geotani}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'villages';" 2>/dev/null | xargs || echo "0")

if [ "$RECORD_COUNT" = "0" ] || [ -z "$RECORD_COUNT" ]; then
    echo "   Database tables not found. Running ETL database loader..."
    if [ -f "data/processed/boundaries/geotani_boundaries.gpkg" ] || [ -f "data/processed/boundaries/taniscope_boundaries.gpkg" ]; then
        docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml run --rm api python -m etl.load_postgis
        echo "   ✓ Initial datasets loaded successfully."
    else
        echo "   ⚠️ Processed GPKG data files not found in data/processed/. Please copy your processed data to the server."
    fi
else
    VILLAGE_ROWS=$(docker exec geotani-prod-db psql -U "${POSTGRES_USER:-geotani}" -d "${POSTGRES_DB:-geotani}" -t -c "SELECT COUNT(*) FROM villages;" 2>/dev/null | xargs || echo "0")
    echo "   ✓ Database already populated with $VILLAGE_ROWS village boundaries."
fi

# 6. Restart tile server to register spatial views
docker restart geotani-prod-tiles > /dev/null 2>&1 || true

# 7. Summary
echo ""
echo "================================================================="
echo "  🎉 GEOTANI PRODUCTION DEPLOYMENT COMPLETE"
echo "================================================================="
echo "  • Web & HTTPS Gateway: https://${DOMAIN_NAME:-geotani.cloud}"
echo "  • Health Endpoint:     https://${DOMAIN_NAME:-geotani.cloud}/health"
echo "  • API Documentation:   https://${DOMAIN_NAME:-geotani.cloud}/docs"
echo "  • Vector Tiles:        https://${DOMAIN_NAME:-geotani.cloud}/tiles/village_suitability/{z}/{x}/{y}"
echo "================================================================="
echo "  Check container status with: docker compose -f docker-compose.prod.yml ps"
echo "  View live logs with:         docker compose -f docker-compose.prod.yml logs -f"
echo ""
