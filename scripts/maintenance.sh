#!/bin/bash

# Universal Text Extractor - Maintenance Script
# Performs routine maintenance tasks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

cd "$APP_DIR"

echo "🔧 Universal Text Extractor - Maintenance Script"
echo "================================================"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --cleanup-data     Clean up old data based on retention policy"
    echo "  --optimize-db      Optimize SQLite database"
    echo "  --check-health     Run health checks"
    echo "  --update-deps      Update Python dependencies"
    echo "  --backup           Create backup"
    echo "  --logs             Show recent logs"
    echo "  --stats            Show usage statistics"
    echo "  --all              Run all maintenance tasks"
    echo "  --help             Show this help message"
}

# Function to cleanup old data
cleanup_data() {
    echo "🧹 Cleaning up old data..."
    
    if [ -f "data/text_extractor.db" ]; then
        python3 -c "
import sys
sys.path.append('.')
from utils.database import cleanup_old_data
deleted = cleanup_old_data(90, 'extraction_logs')
print(f'Deleted {deleted} old extraction records')
deleted = cleanup_old_data(365, 'user_feedback')
print(f'Deleted {deleted} old feedback records')
"
    else
        echo "⚠️  Database not found"
    fi
}

# Function to optimize database
optimize_db() {
    echo "⚡ Optimizing database..."
    
    if [ -f "data/text_extractor.db" ]; then
        sqlite3 data/text_extractor.db "VACUUM; ANALYZE;"
        echo "✅ Database optimized"
    else
        echo "⚠️  Database not found"
    fi
}

# Function to run health checks
check_health() {
    echo "🏥 Running health checks..."
    
    if [ -f "health_check.py" ]; then
        python3 health_check.py
    else
        echo "⚠️  Health check script not found"
    fi
}

# Function to update dependencies
update_deps() {
    echo "📦 Updating dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install --upgrade -r requirements.txt
        echo "✅ Dependencies updated"
    else
        echo "⚠️  Requirements file not found"
    fi
}

# Function to create backup
create_backup() {
    echo "💾 Creating backup..."
    
    if [ -f "scripts/backup.sh" ]; then
        bash scripts/backup.sh --cleanup
    else
        echo "⚠️  Backup script not found"
    fi
}

# Function to show logs
show_logs() {
    echo "📋 Recent application logs..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose logs --tail=50
    elif [ -d "logs" ]; then
        find logs -name "*.log" -exec tail -20 {} \;
    else
        echo "ℹ️  No logs found"
    fi
}

# Function to show statistics
show_stats() {
    echo "📊 Usage statistics..."
    
    if [ -f "data/text_extractor.db" ]; then
        python3 -c "
import sys
sys.path.append('.')
from utils.database import get_analytics_summary
stats = get_analytics_summary()
print(f'Total files processed: {stats[\"total_processed\"]}')
print(f'Success rate: {stats[\"success_rate\"]}%')
print(f'OCR usage: {stats[\"ocr_usage\"]}%')
print(f'Top file types: {stats[\"top_file_types\"][:3]}')
"
    else
        echo "⚠️  Database not found"
    fi
}

# Function to run all maintenance tasks
run_all() {
    echo "🔄 Running all maintenance tasks..."
    cleanup_data
    echo ""
    optimize_db
    echo ""
    check_health
    echo ""
    show_stats
    echo ""
    create_backup
}

# Parse command line arguments
case "${1:-}" in
    --cleanup-data)
        cleanup_data
        ;;
    --optimize-db)
        optimize_db
        ;;
    --check-health)
        check_health
        ;;
    --update-deps)
        update_deps
        ;;
    --backup)
        create_backup
        ;;
    --logs)
        show_logs
        ;;
    --stats)
        show_stats
        ;;
    --all)
        run_all
        ;;
    --help)
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        echo "❌ Unknown option: $1"
        show_usage
        exit 1
        ;;
esac

echo ""
echo "🎉 Maintenance task completed!"