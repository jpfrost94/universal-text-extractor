#!/bin/bash
# Script to package the Text Extraction Tool for on-premises deployment

# Create deployment directory
mkdir -p text_extractor_package
mkdir -p text_extractor_package/utils
mkdir -p text_extractor_package/.streamlit
mkdir -p text_extractor_package/data

# Copy application files
cp app.py text_extractor_package/
cp utils/*.py text_extractor_package/utils/
cp .streamlit/config.toml text_extractor_package/.streamlit/

# Copy deployment files
cp Dockerfile text_extractor_package/
cp docker-compose.yml text_extractor_package/
cp README.md text_extractor_package/
cp deployment_guide.md text_extractor_package/

# Create empty database directory
touch text_extractor_package/data/.keep

# Create a simple startup script
cat > text_extractor_package/start.sh << 'EOF'
#!/bin/bash
# Start the Text Extraction Tool

# Ensure data directory exists
mkdir -p data

# Start the Streamlit app
streamlit run app.py --server.port=5000 --server.address=0.0.0.0
EOF

# Make startup script executable
chmod +x text_extractor_package/start.sh

# Create ZIP archive
zip -r text_extractor_package.zip text_extractor_package

echo "Package created: text_extractor_package.zip"
echo "This package contains everything needed for on-premises deployment."
echo "Follow the instructions in deployment_guide.md to set up the application."