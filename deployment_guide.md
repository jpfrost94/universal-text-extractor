# Text Extraction Tool Deployment Guide

This guide will help you deploy the Text Extraction Tool within your organization's on-premises environment.

## System Requirements

- Python 3.11 or higher
- At least 4GB RAM recommended (more for processing large documents)
- 2GB free disk space
- For OCR functionality: Tesseract OCR installed on the system

## Installation Steps

### 1. Copy Application Files

Copy all application files to your server:
- `app.py`
- `utils/` directory with all its contents
- `.streamlit/config.toml`

### 2. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install streamlit>=1.27.0
pip install pillow>=10.0.0
pip install pytesseract>=0.3.10
pip install pdf2image>=1.16.3
pip install PyPDF2>=3.0.1
pip install python-docx>=0.8.11
pip install python-pptx>=0.6.21
pip install beautifulsoup4>=4.12.2
pip install striprtf>=0.0.22
pip install pandas>=2.0.0
pip install odfpy>=1.4.1
pip install ebooklib>=0.18
pip install extract-msg>=0.41.1
```

### 3. Install System Dependencies

#### For OCR Functionality (Tesseract)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-eng  # English language data
# Add other language packs as needed: tesseract-ocr-fra, tesseract-ocr-deu, etc.
```

**Windows:**
1. Download the installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install and add to PATH
3. Download additional language data as needed

**Red Hat/CentOS:**
```bash
sudo yum install tesseract
sudo yum install tesseract-langpack-eng  # English language data
```

#### For PDF to Image Conversion (Poppler)

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
1. Download from [poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/)
2. Add the bin directory to your PATH

**Red Hat/CentOS:**
```bash
sudo yum install poppler-utils
```

### 4. Run as a Service

#### Using systemd (Linux)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/text-extractor.service
```

Add the following content (adjust paths as needed):

```
[Unit]
Description=Text Extraction Tool
After=network.target

[Service]
User=yourusername
WorkingDirectory=/path/to/app
ExecStart=/path/to/venv/bin/streamlit run app.py --server.port=5000 --server.address=0.0.0.0
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable text-extractor
sudo systemctl start text-extractor
```

#### Using Windows Services

1. Install NSSM (Non-Sucking Service Manager):
   - Download from [NSSM website](https://nssm.cc/download)
   
2. Create a service:
   ```
   nssm install TextExtractor
   ```
   - Set Path to the Python executable in your virtual environment
   - Set Arguments to "-m streamlit run app.py --server.port=5000 --server.address=0.0.0.0"
   - Set Startup directory to your application directory

3. Start the service:
   ```
   nssm start TextExtractor
   ```

### 5. Configure Proxy (Optional but Recommended)

For improved security and performance, place the application behind a reverse proxy like Nginx or Apache.

#### Example Nginx Configuration

```
server {
    listen 80;
    server_name text-extractor.yourdomain.internal;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Initial Configuration

### First-Time Login

1. Access the application at `http://your-server-address:5000` (or the configured URL)
2. Log in with the default credentials:
   - Username: `admin`
   - Password: `admin123`
3. Navigate to Usage Statistics
4. Under User Management, create a new admin account with a secure password
5. Log out and log back in with the new admin account
6. It's recommended to reset statistics before production use

### Data Storage

The application stores:
- User credentials in `users.json`
- Usage statistics in `usage_statistics.json` and `usage_statistics.csv`

These files are created in the application directory. Consider:
- Setting appropriate file permissions
- Including these files in your backup routine
- Mounting a separate volume for data persistence if running in a container

## Troubleshooting

### OCR Not Working

1. Verify Tesseract is installed: `tesseract --version`
2. Check language packs are installed
3. Ensure the application has permission to execute Tesseract

### Server Won't Start

1. Check Python version: `python --version` (should be 3.11+)
2. Verify all dependencies are installed correctly
3. Check the system logs: `sudo journalctl -u text-extractor` (for systemd)
4. Ensure the port is not already in use: `netstat -tuln | grep 5000`

### Authentication Issues

If you lose access to all admin accounts:
1. Stop the service
2. Delete or rename the `users.json` file (a new one will be created with default credentials)
3. Restart the service
4. Log in with the default credentials and create new accounts

## Security Considerations

- Change default admin credentials immediately
- Run the application behind a firewall
- Consider implementing additional authentication via your proxy server
- Use HTTPS if accessible over a network
- Regularly backup and monitor the user credentials file
- Review and clear statistics periodically

## Updating the Application

1. Stop the service
2. Backup the application directory, especially `users.json` and statistics files
3. Replace application files with the new version
4. Start the service

## Support

For internal support, please contact your IT department.