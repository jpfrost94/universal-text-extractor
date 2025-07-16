#!/bin/bash

# Universal Text Extractor - Restore Script
# Restores application data from backup

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Example: $0 backups/text_extractor_backup_20250116_120000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Starting restore process..."
echo "📁 Backup file: $BACKUP_FILE"

# Create temporary directory
TEMP_DIR="/tmp/text_extractor_restore_$$"
mkdir -p "$TEMP_DIR"

echo "📦 Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Find the backup directory (should be the only directory in temp)
BACKUP_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "text_extractor_backup_*" | head -1)

if [ -z "$BACKUP_DIR" ]; then
    echo "❌ Invalid backup file structure"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "📋 Backup manifest:"
if [ -f "$BACKUP_DIR/backup_manifest.txt" ]; then
    cat "$BACKUP_DIR/backup_manifest.txt"
    echo ""
fi

# Confirm restore
read -p "⚠️  This will overwrite existing data. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "🛑 Stopping application..."
if command -v docker-compose &> /dev/null; then
    docker-compose down 2>/dev/null || true
fi

echo "💾 Creating backup of current data..."
if [ -d "data" ]; then
    mv data "data.backup.$(date +%Y%m%d_%H%M%S)" || true
fi

echo "📁 Restoring data directory..."
if [ -d "$BACKUP_DIR/data" ]; then
    cp -r "$BACKUP_DIR/data" .
    echo "✅ Data directory restored"
else
    echo "⚠️  No data directory in backup"
fi

echo "📊 Restoring database..."
if [ -f "$BACKUP_DIR/database_backup.db" ]; then
    mkdir -p data
    cp "$BACKUP_DIR/database_backup.db" "data/text_extractor.db"
    echo "✅ Database restored"
else
    echo "⚠️  No database backup found"
fi

echo "📝 Restoring configuration..."
if [ -d "$BACKUP_DIR/.streamlit" ]; then
    cp -r "$BACKUP_DIR/.streamlit" .
    echo "✅ Streamlit configuration restored"
fi

if [ -f "$BACKUP_DIR/.env" ]; then
    cp "$BACKUP_DIR/.env" .
    echo "✅ Environment configuration restored"
fi

# Set proper permissions
chmod -R 755 data/ 2>/dev/null || true

echo "🚀 Starting application..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
    echo "✅ Application started with Docker"
else
    echo "ℹ️  Start the application manually with: streamlit run app.py"
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo "🎉 Restore completed successfully!"
echo ""
echo "Next steps:"
echo "1. Verify the application is running"
echo "2. Test login functionality"
echo "3. Check data integrity"
echo "4. Remove backup files if no longer needed"