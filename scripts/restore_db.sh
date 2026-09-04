#!/usr/bin/env bash
# ==============================================================================
# GeoTani — Database Restore Utility
# Usage: ./scripts/restore_db.sh <backup_file.sql.gz>
# ==============================================================================

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file '$BACKUP_FILE' does not exist."
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

ENV_FILE=".env.prod"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

DB_CONTAINER="${DB_CONTAINER:-geotani-prod-db}"
DB_USER="${POSTGRES_USER:-geotani}"
DB_NAME="${POSTGRES_DB:-geotani}"

echo "Restoring GeoTani database ($DB_NAME) from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"

# Restart tile server to reload spatial view metadata
docker restart geotani-prod-tiles > /dev/null 2>&1 || true

echo "✓ Database restored successfully and tile server refreshed."
