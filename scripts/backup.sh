#!/bin/bash

# Universal Text Extractor - Backup Script
# Creates backups of application data and configuration

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="text_extractor_backup_${TIMESTAMP}"

echo "🔄 Starting backup process..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create temporary backup directory
TEMP_BACKUP_DIR="/tmp/${BACKUP_NAME}"
mkdir -p "$TEMP_BACKUP_DIR"

echo "📁 Backing up data directory..."
if [ -d "data" ]; then
    cp -r data "$TEMP_BACKUP_DIR/"
else
    echo "⚠️  Data directory not found"
fi

echo "📊 Backing up database..."
if [ -f "data/text_extractor.db" ]; then
    sqlite3 data/text_extractor.db ".backup $TEMP_BACKUP_DIR/database_backup.db"
else
    echo "⚠️  Database file not found"
fi

echo "📝 Backing up configuration..."
cp -r .streamlit "$TEMP_BACKUP_DIR/" 2>/dev/null || echo "⚠️  Streamlit config not found"
cp .env "$TEMP_BACKUP_DIR/" 2>/dev/null || echo "ℹ️  No .env file found"
cp docker-compose.yml "$TEMP_BACKUP_DIR/" 2>/dev/null || true
cp docker-compose.prod.yml "$TEMP_BACKUP_DIR/" 2>/dev/null || true

echo "📋 Creating backup manifest..."
cat > "$TEMP_BACKUP_DIR/backup_manifest.txt" << EOF
Universal Text Extractor Backup
Created: $(date)
Hostname: $(hostname)
Version: 1.0.0

Contents:
- Application data directory
- SQLite database
- Configuration files
- Docker compose files

Restore Instructions:
1. Stop the application
2. Extract backup to application directory
3. Restore data directory: cp -r data_backup/* data/
4. Restore database: cp database_backup.db data/text_extractor.db
5. Restart the application
EOF

echo "🗜️  Creating compressed archive..."
cd /tmp
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
mv "${BACKUP_NAME}.tar.gz" "$(pwd)/$BACKUP_DIR/"

# Cleanup
rm -rf "$TEMP_BACKUP_DIR"

echo "✅ Backup completed: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"

# Optional: Clean up old backups (keep last 7 days)
if [ "$1" = "--cleanup" ]; then
    echo "🧹 Cleaning up old backups..."
    find "$BACKUP_DIR" -name "text_extractor_backup_*.tar.gz" -mtime +7 -delete
    echo "✅ Old backups cleaned up"
fi

echo "🎉 Backup process finished!"