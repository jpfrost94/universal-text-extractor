# Universal Text Extractor - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Docker (Recommended)

1. **Clone or download this repository**
2. **Start the application:**
   ```bash
   docker-compose up -d
   ```
3. **Access the application:** http://localhost:5000
4. **Login with default credentials:**
   - Username: `admin`
   - Password: `admin123`
5. **⚠️ IMPORTANT:** Change the default password immediately!

### Option 2: Manual Installation

#### Prerequisites
- Python 3.11 or higher
- Tesseract OCR (for image text extraction)

#### Installation Steps

**Linux/Mac:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the application
streamlit run app.py --server.port=5000 --server.address=0.0.0.0
```

**Windows:**
```cmd
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the application
streamlit run app.py --server.port=5000 --server.address=0.0.0.0
```

## 📋 What You Can Do

- **Extract text from PDFs** (including scanned documents with OCR)
- **Process Office documents** (Word, PowerPoint, Excel)
- **Handle images** with OCR text recognition
- **Export results** in TXT, CSV, or JSON formats
- **Track usage statistics** (admin users)
- **Manage users** and permissions

## 🔧 System Requirements

- **Memory:** 4GB RAM recommended
- **Storage:** 2GB free space
- **Network:** Port 5000 (configurable)

## 🛡️ Security Notes

1. **Change default admin password immediately**
2. **Deploy behind your firewall**
3. **Consider using HTTPS in production**
4. **Regular backups of user data**

## 📚 Need More Help?

- See `deployment_guide.md` for detailed setup instructions
- Check `README.md` for comprehensive documentation
- Review Docker configuration in `docker-compose.yml`

## 🐛 Troubleshooting

**OCR not working?**
- Install Tesseract: `sudo apt-get install tesseract-ocr` (Linux)
- Windows: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

**Can't access the application?**
- Check if port 5000 is available: `netstat -tuln | grep 5000`
- Try a different port: `streamlit run app.py --server.port=8501`

**Docker issues?**
- Ensure Docker is running
- Check logs: `docker-compose logs`