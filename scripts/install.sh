#!/bin/bash

# Universal Text Extractor - Installation Script for Linux/Mac

set -e

echo "🚀 Universal Text Extractor - Installation Script"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. Consider using a regular user account."
fi

# Check Python version
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
    REQUIRED_VERSION="3.11"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python 3.11+ is required. Found: $PYTHON_VERSION"
        print_info "Please install Python 3.11 or higher and try again."
        exit 1
    fi
    print_status "Python $PYTHON_VERSION found"
else
    print_error "Python 3 not found. Please install Python 3.11+ and try again."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 not found. Please install pip and try again."
    exit 1
fi

# Install system dependencies
print_info "Installing system dependencies..."

if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    print_info "Detected Debian/Ubuntu system"
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils libgl1-mesa-glx
    print_status "System dependencies installed"
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    print_info "Detected CentOS/RHEL system"
    sudo yum install -y tesseract poppler-utils mesa-libGL
    print_status "System dependencies installed"
elif command -v brew &> /dev/null; then
    # macOS with Homebrew
    print_info "Detected macOS with Homebrew"
    brew install tesseract poppler
    print_status "System dependencies installed"
else
    print_warning "Could not detect package manager. Please install manually:"
    print_info "- Tesseract OCR"
    print_info "- Poppler utilities"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
print_info "Creating Python virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Removing..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate
print_status "Virtual environment created"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip
print_status "Pip upgraded"

# Install Python dependencies
print_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Create necessary directories
print_info "Creating application directories..."
mkdir -p data logs backups
print_status "Directories created"

# Set permissions
chmod 755 data logs backups
chmod +x scripts/*.sh 2>/dev/null || true

# Create systemd service file (optional)
if command -v systemctl &> /dev/null; then
    read -p "Create systemd service? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SERVICE_FILE="/etc/systemd/system/text-extractor.service"
        CURRENT_DIR=$(pwd)
        CURRENT_USER=$(whoami)
        
        sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Universal Text Extractor
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/streamlit run app.py --server.port=5000 --server.address=0.0.0.0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable text-extractor
        print_status "Systemd service created and enabled"
        print_info "Start with: sudo systemctl start text-extractor"
    fi
fi

# Run health check
print_info "Running health check..."
if python3 health_check.py; then
    print_status "Health check passed"
else
    print_warning "Health check failed. Check the output above."
fi

print_status "Installation completed successfully!"
echo ""
echo "🎉 Universal Text Extractor is ready to use!"
echo ""
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  streamlit run app.py --server.port=5000 --server.address=0.0.0.0"
echo ""
echo "Or if you created a systemd service:"
echo "  sudo systemctl start text-extractor"
echo ""
echo "Access the application at: http://localhost:5000"
echo "Default login: admin / admin123"
echo ""
print_warning "Remember to change the default password immediately!"
echo ""
echo "For more information, see:"
echo "- README.md for comprehensive documentation"
echo "- QUICK_START.md for quick setup guide"
echo "- deployment_guide.md for production deployment"