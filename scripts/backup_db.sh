#!/usr/bin/env bash
# ==============================================================================
# GeoTani — Automated Database Backup Script
# Usage: ./scripts/backup_db.sh [backup_dir]
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

BACKUP_DIR="${1:-$PROJECT_ROOT/backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/geotani_db_${TIMESTAMP}.sql.gz"

ENV_FILE=".env.prod"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

DB_CONTAINER="${DB_CONTAINER:-geotani-prod-db}"
DB_USER="${POSTGRES_USER:-geotani}"
DB_NAME="${POSTGRES_DB:-geotani}"

echo "Backing up GeoTani database ($DB_NAME) from $DB_CONTAINER..."
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --no-owner --clean | gzip > "$BACKUP_FILE"

FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✓ Backup created successfully: $BACKUP_FILE ($FILE_SIZE)"

# Clean up backups older than 14 days
find "$BACKUP_DIR" -name "geotani_db_*.sql.gz" -mtime +14 -exec rm {} \;
echo "✓ Rotated backups older than 14 days."
