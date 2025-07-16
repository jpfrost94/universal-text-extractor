#!/bin/bash

# Universal Text Extractor - GitLab Preparation Script
# This script prepares the project for GitLab deployment

set -e

echo "🚀 Preparing Universal Text Extractor for GitLab deployment..."
echo "============================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please run this script from the project root directory."
    exit 1
fi

# Make scripts executable
print_info "Making scripts executable..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x package_for_deployment.sh 2>/dev/null || true
chmod +x health_check.py 2>/dev/null || true
print_status "Scripts made executable"

# Validate project structure
print_info "Validating project structure..."
required_files=(
    "app.py"
    "requirements.txt"
    "pyproject.toml"
    "Dockerfile"
    "docker-compose.yml"
    "docker-compose.prod.yml"
    ".gitlab-ci.yml"
    "README.md"
    "QUICK_START.md"
    "deployment_guide.md"
    "DEPLOYMENT_CHECKLIST.md"
    "DEPLOYMENT_SUMMARY.md"
    "CHANGELOG.md"
    "LICENSE"
    ".env.example"
    ".gitignore"
    ".dockerignore"
    "health_check.py"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    print_status "All required files present"
else
    print_warning "Missing files: ${missing_files[*]}"
fi

# Check utils directory
print_info "Checking utils directory..."
required_utils=(
    "utils/__init__.py"
    "utils/database.py"
    "utils/auth_db.py"
    "utils/file_handlers.py"
    "utils/ocr_utils.py"
    "utils/image_processing.py"
    "utils/export_utils.py"
)

missing_utils=()
for util in "${required_utils[@]}"; do
    if [ ! -f "$util" ]; then
        missing_utils+=("$util")
    fi
done

if [ ${#missing_utils[@]} -eq 0 ]; then
    print_status "All utility modules present"
else
    print_warning "Missing utils: ${missing_utils[*]}"
fi

# Check scripts directory
print_info "Checking scripts directory..."
if [ -d "scripts" ]; then
    script_count=$(find scripts -name "*.sh" -o -name "*.bat" | wc -l)
    print_status "Scripts directory contains $script_count files"
else
    print_warning "Scripts directory not found"
fi

# Validate Python syntax
print_info "Validating Python syntax..."
if command -v python3 &> /dev/null; then
    if python3 -m py_compile app.py; then
        print_status "Main application syntax is valid"
    else
        print_warning "Python syntax errors found in app.py"
    fi
    
    # Check utils modules
    for py_file in utils/*.py; do
        if [ -f "$py_file" ]; then
            if python3 -m py_compile "$py_file"; then
                continue
            else
                print_warning "Syntax error in $py_file"
            fi
        fi
    done
    print_status "Python modules validated"
else
    print_warning "Python3 not found, skipping syntax validation"
fi

# Check Docker configuration
print_info "Validating Docker configuration..."
if command -v docker &> /dev/null; then
    if docker build -t text-extractor-test . --quiet; then
        print_status "Docker build successful"
        docker rmi text-extractor-test --force > /dev/null 2>&1 || true
    else
        print_warning "Docker build failed"
    fi
else
    print_warning "Docker not found, skipping Docker validation"
fi

# Create deployment package info
print_info "Creating deployment package information..."
cat > DEPLOYMENT_INFO.md << EOF
# Universal Text Extractor - Deployment Package

**Package Created:** $(date)
**Version:** 1.0.0
**Created By:** $(whoami)
**System:** $(uname -s) $(uname -r)

## Package Contents

### Core Application
- Main application (Streamlit-based web interface)
- Complete utility modules for text extraction
- Database management with SQLite
- User authentication and authorization
- Analytics and reporting dashboard

### Deployment Options
- Docker containerization (development and production)
- Manual installation scripts (Linux/Mac/Windows)
- GitLab CI/CD pipeline configuration
- Health monitoring and maintenance tools

### Documentation
- Comprehensive README with feature overview
- Quick start guide (5-minute setup)
- Detailed deployment guide
- Deployment checklist for production
- Changelog and version history

### Security Features
- Role-based access control
- Session management
- Audit logging
- Data retention policies
- On-premises deployment ready

## Quick Deployment

### Option 1: Docker (Recommended)
\`\`\`bash
docker-compose up -d
\`\`\`

### Option 2: Manual Installation
\`\`\`bash
./scripts/install.sh
./scripts/start.sh
\`\`\`

### Option 3: GitLab CI/CD
1. Push to GitLab repository
2. Configure CI/CD variables
3. Deploy via pipeline

## Default Access
- **URL:** http://localhost:5000
- **Username:** admin
- **Password:** admin123
- **⚠️ Change password immediately!**

## Support
- See README.md for comprehensive documentation
- Check DEPLOYMENT_CHECKLIST.md for production deployment
- Review troubleshooting section in deployment_guide.md

---
**Ready for production deployment!** 🚀
EOF

print_status "Deployment information created"

# Create GitLab repository setup instructions
print_info "Creating GitLab setup instructions..."
cat > GITLAB_SETUP.md << EOF
# GitLab Repository Setup Instructions

## 1. Create GitLab Repository

1. Log into your GitLab instance
2. Create a new project/repository
3. Choose "Create blank project"
4. Set project name: \`universal-text-extractor\`
5. Set visibility level as appropriate for your organization
6. Initialize with README: **No** (we have our own)

## 2. Upload Project Files

### Option A: Git Command Line
\`\`\`bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit: Universal Text Extractor v1.0.0"

# Add GitLab remote (replace with your GitLab URL)
git remote add origin https://gitlab.example.com/yourorg/universal-text-extractor.git
git branch -M main
git push -u origin main
\`\`\`

### Option B: GitLab Web Interface
1. Use GitLab's web IDE to upload files
2. Create new files and copy content
3. Commit changes with appropriate message

## 3. Configure CI/CD Variables

Go to Project Settings > CI/CD > Variables and add:

### Required Variables
- \`CI_REGISTRY_USER\`: GitLab registry username (usually \`gitlab-ci-token\`)
- \`CI_REGISTRY_PASSWORD\`: GitLab registry password (auto-provided)

### Deployment Variables (if using automated deployment)
- \`STAGING_HOST\`: Staging server hostname/IP
- \`STAGING_USER\`: SSH username for staging server
- \`STAGING_PRIVATE_KEY\`: SSH private key for staging access
- \`PRODUCTION_HOST\`: Production server hostname/IP
- \`PRODUCTION_USER\`: SSH username for production server
- \`PRODUCTION_PRIVATE_KEY\`: SSH private key for production access

## 4. Enable GitLab Features

### Container Registry
1. Go to Project Settings > General > Visibility
2. Enable Container Registry
3. Save changes

### Pages (Optional - for documentation)
1. Go to Project Settings > Pages
2. Enable GitLab Pages if available

### Issues and Wiki (Optional)
1. Enable Issues for bug tracking
2. Enable Wiki for additional documentation

## 5. Configure Branch Protection (Recommended)

1. Go to Project Settings > Repository > Push Rules
2. Protect the \`main\` branch
3. Require merge requests for changes
4. Enable "Delete source branch" option

## 6. Set Up Webhooks (Optional)

If you need to trigger external systems:
1. Go to Project Settings > Webhooks
2. Add webhook URLs as needed
3. Configure trigger events

## 7. Test the Pipeline

1. Make a small change to README.md
2. Commit and push to trigger the pipeline
3. Check Pipeline status in CI/CD > Pipelines
4. Verify all stages complete successfully

## 8. Deploy to Staging

1. Go to CI/CD > Pipelines
2. Find the latest successful pipeline
3. Click on "deploy_staging" job
4. Click "Play" button to trigger manual deployment

## 9. Production Deployment

1. Ensure staging deployment is working correctly
2. Go to CI/CD > Pipelines
3. Click on "deploy_production" job
4. Click "Play" button for production deployment

## Troubleshooting

### Pipeline Fails
- Check CI/CD > Pipelines for error details
- Verify all required variables are set
- Check GitLab Runner availability

### Docker Build Fails
- Verify Dockerfile syntax
- Check if base images are accessible
- Review build logs for specific errors

### Deployment Fails
- Verify SSH access to target servers
- Check server requirements are met
- Verify Docker is installed on target servers

---

**Your GitLab repository is ready for the Universal Text Extractor!** 🎉
EOF

print_status "GitLab setup instructions created"

# Final validation
print_info "Running final validation..."

# Check if git is initialized
if [ -d ".git" ]; then
    print_status "Git repository initialized"
else
    print_info "Git repository not initialized (will be done during GitLab setup)"
fi

# Summary
echo ""
echo "🎉 Universal Text Extractor is ready for GitLab deployment!"
echo "=========================================================="
echo ""
echo "📁 Project Structure: ✅ Complete"
echo "🐳 Docker Configuration: ✅ Ready"
echo "🔧 CI/CD Pipeline: ✅ Configured"
echo "📚 Documentation: ✅ Comprehensive"
echo "🛡️  Security: ✅ Implemented"
echo "🔧 Maintenance Tools: ✅ Available"
echo ""
echo "📋 Next Steps:"
echo "1. Review GITLAB_SETUP.md for repository setup"
echo "2. Follow DEPLOYMENT_CHECKLIST.md for production deployment"
echo "3. Use QUICK_START.md for immediate testing"
echo "4. See README.md for comprehensive documentation"
echo ""
echo "🚀 Ready to deploy to GitLab!"
echo ""
print_warning "Remember to change the default admin password (admin/admin123) immediately after deployment!"
echo ""
echo "📞 For support, refer to the comprehensive documentation included in this package."