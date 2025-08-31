#!/bin/bash

# ECOMSIMPLY Backup Script
# Usage: ./scripts/backup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "💾 Starting ECOMSIMPLY backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup MongoDB
echo "📁 Backing up MongoDB..."
docker exec ecomsimply_mongodb mongodump --out /tmp/backup_$TIMESTAMP
docker cp ecomsimply_mongodb:/tmp/backup_$TIMESTAMP "$BACKUP_DIR/mongodb_$TIMESTAMP"
docker exec ecomsimply_mongodb rm -rf /tmp/backup_$TIMESTAMP

# Backup Redis (if needed)
echo "📊 Backing up Redis..."
docker exec ecomsimply_redis redis-cli BGSAVE
docker cp ecomsimply_redis:/data/dump.rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"

# Backup application logs
echo "📄 Backing up logs..."
cp -r "$PROJECT_DIR/logs" "$BACKUP_DIR/logs_$TIMESTAMP" 2>/dev/null || true

# Create compressed archive
echo "🗜️ Creating compressed archive..."
cd "$BACKUP_DIR"
tar -czf "ecomsimply_backup_$TIMESTAMP.tar.gz" mongodb_$TIMESTAMP redis_$TIMESTAMP.rdb logs_$TIMESTAMP 2>/dev/null || tar -czf "ecomsimply_backup_$TIMESTAMP.tar.gz" mongodb_$TIMESTAMP redis_$TIMESTAMP.rdb

# Clean up individual directories
rm -rf mongodb_$TIMESTAMP redis_$TIMESTAMP.rdb logs_$TIMESTAMP 2>/dev/null || true

# Remove old backups (keep last 7 days)
find "$BACKUP_DIR" -name "ecomsimply_backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "✅ Backup completed: $BACKUP_DIR/ecomsimply_backup_$TIMESTAMP.tar.gz"

# Upload to S3 if configured
if [ -n "$BACKUP_S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
    echo "☁️ Uploading to S3..."
    aws s3 cp "$BACKUP_DIR/ecomsimply_backup_$TIMESTAMP.tar.gz" "s3://$BACKUP_S3_BUCKET/backups/"
    echo "✅ Backup uploaded to S3"
fi