FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    tesseract-ocr-spa \
    tesseract-ocr-ita \
    tesseract-ocr-por \
    poppler-utils \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Copy application files
COPY app.py /app/
COPY utils/ /app/utils/
COPY .streamlit/ /app/.streamlit/

# Set permissions for SQLite database directory
RUN chmod 777 /app/data

# Install Python dependencies
RUN pip install --no-cache-dir \
    streamlit>=1.27.0 \
    pillow>=10.0.0 \
    pytesseract>=0.3.10 \
    pdf2image>=1.16.3 \
    PyPDF2>=3.0.1 \
    python-docx>=0.8.11 \
    python-pptx>=0.6.21 \
    beautifulsoup4>=4.12.2 \
    striprtf>=0.0.22 \
    pandas>=2.0.0 \
    odfpy>=1.4.1 \
    ebooklib>=0.18 \
    extract-msg>=0.41.1

# Set environment variables for Tesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Modify analytics utils to use data directory
RUN sed -i 's|ANALYTICS_FILE = "usage_statistics.json"|ANALYTICS_FILE = "/app/data/usage_statistics.json"|g' /app/utils/analytics.py \
    && sed -i 's|CSV_EXPORT_FILE = "usage_statistics.csv"|CSV_EXPORT_FILE = "/app/data/usage_statistics.csv"|g' /app/utils/analytics.py \
    && sed -i 's|USERS_FILE = "users.json"|USERS_FILE = "/app/data/users.json"|g' /app/utils/auth.py

# Expose port
EXPOSE 5000

# Set command
CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0"]