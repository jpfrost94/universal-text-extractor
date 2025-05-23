# Text Extraction Tool

A comprehensive tool for extracting text from various document formats with OCR capabilities, designed for secure on-premises deployment within organizations.

## Features

- Extract text from multiple file formats (PDF, Office documents, images, etc.)
- OCR processing for images and scanned documents
- Image preprocessing for improved OCR results
- Export extracted text to various formats (TXT, CSV, JSON)
- Usage statistics tracking (anonymized)
- Role-based access control
- Admin dashboard for monitoring usage

## Deployment Options

This package includes multiple deployment options:

1. **Standard Installation**
   - Detailed in `deployment_guide.md`
   - Suitable for direct installation on Windows/Linux servers

2. **Docker Deployment**
   - Using included `Dockerfile` and `docker-compose.yml`
   - Ideal for containerized environments
   - Includes all dependencies pre-configured

## Quick Start

See `deployment_guide.md` for comprehensive setup instructions.

### Docker Quick Start

1. Create a data directory for persistent storage:
   ```bash
   mkdir -p data
   ```

2. Build and start the container:
   ```bash
   docker-compose up -d
   ```

3. Access the application at `http://localhost:5000`

4. Log in with default credentials:
   - Username: `admin`
   - Password: `admin123`

5. **Important:** Create a new admin account immediately

## Security Considerations

- Change default admin password immediately after first login
- Deploy behind your organization's firewall
- Consider using a reverse proxy with HTTPS for encrypted connections
- Regular backups of user and statistics data

## System Requirements

- Python 3.11+ (for standard installation)
- Docker (for container deployment)
- Tesseract OCR (included in Docker image)
- 4GB RAM recommended
- 2GB disk space