#!/bin/bash

# Universal Text Extractor - Start Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

cd "$APP_DIR"

echo "🚀 Starting Universal Text Extractor..."

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Run install.sh first."
    exit 1
fi

# Check if required files exist
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data logs

# Set default port if not specified
PORT=${PORT:-5000}
HOST=${HOST:-0.0.0.0}

echo "🌐 Starting application on http://$HOST:$PORT"
echo "📊 Data directory: $(pwd)/data"
echo "📝 Logs directory: $(pwd)/logs"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Start the application
streamlit run app.py --server.port=$PORT --server.address=$HOST