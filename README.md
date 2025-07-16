# Universal Text Extractor

A comprehensive, enterprise-ready tool for extracting text from various document formats with advanced OCR capabilities. Designed for secure deployment in any environment.

## ✨ Features

### Document Processing
- **PDF Processing**: Extract text from regular and scanned PDFs
- **Office Documents**: Word (.doc, .docx), PowerPoint (.ppt, .pptx), Excel (.xls, .xlsx)
- **Images**: JPG, PNG, TIFF, BMP with OCR text recognition
- **Web Formats**: HTML, XML with clean text extraction
- **Rich Text**: RTF, ODT, ODP, and other formats
- **Email**: EML and MSG file support
- **E-books**: EPUB format support

### Advanced Capabilities
- **OCR Processing**: Tesseract and EasyOCR support with multiple languages
- **Image Enhancement**: Preprocessing for better OCR accuracy
- **Batch Processing**: Handle multiple files efficiently
- **Export Options**: TXT, CSV, JSON formats
- **Usage Analytics**: Comprehensive statistics and reporting
- **User Management**: Role-based access control
- **Data Retention**: Configurable data lifecycle management

### Security & Compliance
- **Secure deployment** - your data stays under your control
- **User authentication** with role-based permissions
- **Audit logging** for compliance requirements
- **Data encryption** and secure file handling
- **Configurable retention policies**

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
# Clone the repository
git clone <your-repo-url>
cd universal-text-extractor

# Start with Docker
docker-compose up -d

# Access at http://localhost:5000
# Default login: admin / admin123
```

### Option 2: Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
streamlit run app.py --server.port=5000 --server.address=0.0.0.0
```

## 📋 System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **OS**: Linux, Windows, or macOS
- **Python**: 3.11+ (for manual installation)

### Dependencies
- **Tesseract OCR**: For image text extraction
- **Poppler**: For PDF to image conversion
- **Docker**: For containerized deployment (optional)

## 🛠️ Installation Options

### Production Deployment
See `deployment_guide.md` for comprehensive production setup instructions including:
- System service configuration
- Reverse proxy setup (Nginx/Apache)
- SSL/TLS configuration
- Backup and monitoring setup

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install -e .[dev]

# Run tests
pytest

# Code formatting
black .
flake8 .
```

## 📊 Supported File Formats

| Category | Formats | OCR Support |
|----------|---------|-------------|
| **Documents** | PDF, DOC, DOCX, RTF, ODT, TXT | ✅ (for scanned) |
| **Images** | JPG, PNG, TIFF, BMP, GIF, WEBP, HEIC | ✅ |
| **Presentations** | PPT, PPTX, ODP | ❌ |
| **Spreadsheets** | XLS, XLSX, ODS, CSV | ❌ |
| **Web** | HTML, HTM, XML | ❌ |
| **Email** | EML, MSG | ❌ |
| **E-books** | EPUB | ❌ |

## 🔧 Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
# Server settings
SERVER_PORT=5000
SERVER_HOST=0.0.0.0

# OCR settings
DEFAULT_OCR_LANGUAGE=eng
TESSERACT_CMD=tesseract

# Security
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT=3600

# File limits
MAX_FILE_SIZE_MB=50
```

### Docker Configuration
- **Development**: `docker-compose.yml`
- **Production**: `docker-compose.prod.yml`

## 🛡️ Security

### Authentication
- Default admin account (change password immediately!)
- Role-based access control (Admin/User)
- Session management with configurable timeout

### Data Protection
- All processing happens locally (no external API calls)
- Configurable data retention policies
- Secure file handling and cleanup
- Audit logging for compliance

### Network Security
- Designed for internal network deployment
- HTTPS support via reverse proxy
- Configurable CORS settings

## 📈 Usage Analytics

### For Administrators
- Total files processed
- Success/failure rates
- OCR usage statistics
- File type distribution
- User activity monitoring
- Performance metrics

### For Users
- Personal processing history
- File type preferences
- Usage trends
- Data export capabilities

## 🔄 GitLab CI/CD

Includes complete GitLab CI/CD configuration:
- **Testing**: Automated code validation
- **Building**: Docker image creation
- **Deployment**: Staging and production pipelines

### Pipeline Stages
1. **Test**: Code validation and dependency checks
2. **Build**: Docker image creation and registry push
3. **Deploy**: Automated deployment to staging/production

## 📚 Documentation

- **`QUICK_START.md`**: Get running in 5 minutes
- **`deployment_guide.md`**: Comprehensive deployment instructions
- **`CHANGELOG.md`**: Version history and updates
- **API Documentation**: Available at `/docs` when running

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Troubleshooting
- Check `deployment_guide.md` for common issues
- Review Docker logs: `docker-compose logs`
- Verify system requirements and dependencies

### Getting Help
- Create an issue in the repository
- Check existing documentation
- Contact your system administrator

## 🏢 Enterprise Features

- **High Availability**: Multi-instance deployment support
- **Load Balancing**: Horizontal scaling capabilities
- **Monitoring**: Health checks and metrics endpoints
- **Backup**: Automated data backup solutions
- **Integration**: API endpoints for system integration

---

**Ready to deploy?** Start with `QUICK_START.md` or use the automated deployment script:
```bash
./package_for_deployment.sh
```