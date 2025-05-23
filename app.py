import streamlit as st
import os
import tempfile
import time
from datetime import datetime
import base64
from utils.file_handlers import (
    detect_file_type, extract_text_from_file, 
    SUPPORTED_FILE_TYPES, SUPPORTED_IMAGE_FORMATS
)
from utils.export_utils import export_text
from utils.ocr_utils import is_ocr_available, get_available_ocr_backends
from utils.image_processing import preprocess_image

# Page configuration
st.set_page_config(
    page_title="Document Text Extractor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state variables if they don't exist
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""
if 'file_name' not in st.session_state:
    st.session_state.file_name = ""
if 'file_type' not in st.session_state:
    st.session_state.file_type = ""
if 'extraction_time' not in st.session_state:
    st.session_state.extraction_time = None
if 'extraction_status' not in st.session_state:
    st.session_state.extraction_status = None
if 'ocr_used' not in st.session_state:
    st.session_state.ocr_used = False
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []

def add_log(message, level="info"):
    """Add a timestamped log message to the session state."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.append({
        "timestamp": timestamp,
        "message": message,
        "level": level
    })

def clear_logs():
    """Clear all log messages."""
    st.session_state.log_messages = []

def format_file_types():
    """Format the supported file types for display."""
    result = {}
    for category, extensions in SUPPORTED_FILE_TYPES.items():
        result[category] = ", ".join([f"*.{ext}" for ext in extensions])
    return result

# Sidebar
with st.sidebar:
    st.title("Text Extraction Tool")
    
    # OCR availability info
    ocr_available = is_ocr_available()
    ocr_backends = get_available_ocr_backends()
    
    st.info(f"📋 Extract text from various document formats")
    
    # Display OCR status
    if ocr_available:
        st.success(f"✅ OCR is available using: {', '.join(ocr_backends)}")
    else:
        st.warning("⚠️ OCR capabilities are not available. Some files may not be processed correctly.")
    
    # Supported file types
    with st.expander("Supported File Types", expanded=False):
        formatted_types = format_file_types()
        for category, extensions in formatted_types.items():
            st.markdown(f"**{category}**: {extensions}")
    
    # About section
    with st.expander("About", expanded=False):
        st.markdown("""
        This tool extracts text from various document formats, including PDFs, 
        images, Office documents, and more. For image-based documents, 
        OCR (Optical Character Recognition) will be used when available.
        
        Use this tool to:
        - Extract text from documents
        - Convert documents to plain text
        - Perform OCR on images or scanned PDFs
        - Export in different formats
        
        For issues or questions, please contact your IT department.
        """)

# Main area
st.title("Document Text Extractor")

# File uploader
uploaded_file = st.file_uploader(
    "Upload a document to extract text", 
    type=sum(SUPPORTED_FILE_TYPES.values(), []),
    help="Upload a file to extract text from it."
)

# OCR and image processing options
show_advanced = False
use_ocr = False
ocr_language = "eng"
enhance_image = False
grayscale = False
contrast_enhancement = 1.0
threshold_value = 128
noise_reduction = False

# Only show advanced options if a file is uploaded
if uploaded_file:
    show_advanced = st.checkbox("Show advanced options", value=False)

# Advanced options UI
if show_advanced and uploaded_file:
    # Detect if the uploaded file is an image or might need OCR
    file_ext = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')
    
    is_image = file_ext in SUPPORTED_IMAGE_FORMATS
    might_need_ocr = is_image or file_ext == 'pdf'
    
    # Only show OCR options if OCR is available and the file might need it
    if might_need_ocr and ocr_available:
        st.subheader("OCR Options")
        col1, col2 = st.columns(2)
        
        with col1:
            use_ocr = st.checkbox("Use OCR", value=True,
                                help="Use Optical Character Recognition to extract text from images or scanned documents")
        
        with col2:
            ocr_language = st.selectbox("OCR Language", ["eng", "fra", "deu", "spa", "ita", "por", "chi_sim", "jpn", "kor"],
                                    help="Select the language of the text to be recognized")
    
    # Image preprocessing options (only for images or if using OCR)
    if is_image or (might_need_ocr and use_ocr):
        st.subheader("Image Preprocessing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            enhance_image = st.checkbox("Enhance Image", value=False,
                                    help="Apply image enhancement techniques to improve OCR results")
            grayscale = st.checkbox("Convert to Grayscale", value=True,
                                help="Convert image to grayscale before processing")
        
        with col2:
            contrast_enhancement = st.slider("Contrast", 0.5, 2.0, 1.0, 0.1,
                                        help="Adjust image contrast to improve text visibility")
            if enhance_image:
                threshold_value = st.slider("Threshold", 0, 255, 128, 1,
                                        help="Threshold value for binarization")
                noise_reduction = st.checkbox("Reduce Noise", value=True,
                                        help="Apply noise reduction filters")

# Process Button
process_clicked = st.button("Process Document", type="primary", use_container_width=True)

# Process the file when button is clicked
if process_clicked and uploaded_file is not None:
    # Clear previous results
    st.session_state.extracted_text = ""
    st.session_state.file_name = uploaded_file.name
    st.session_state.extraction_status = "Processing"
    clear_logs()
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Create a temporary file to process
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{os.path.splitext(uploaded_file.name)[1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Update progress
        status_text.text("Detecting file type...")
        progress_bar.progress(10)
        time.sleep(0.5)  # Small delay for UI feedback
        
        # Detect file type
        file_type = detect_file_type(tmp_file_path)
        st.session_state.file_type = file_type
        add_log(f"Detected file type: {file_type}")
        
        # Update progress
        status_text.text(f"Extracting text from {file_type} file...")
        progress_bar.progress(30)
        
        # Image preprocessing parameters
        preprocess_params = {
            "enhance": enhance_image,
            "grayscale": grayscale,
            "contrast": contrast_enhancement,
            "threshold": threshold_value,
            "noise_reduction": noise_reduction
        } if enhance_image else None
        
        # Extract text
        start_time = time.time()
        extracted_text, ocr_used, log_msgs = extract_text_from_file(
            tmp_file_path, 
            file_type=file_type,
            use_ocr=use_ocr if ocr_available else False,
            ocr_language=ocr_language,
            preprocess_params=preprocess_params
        )
        elapsed_time = time.time() - start_time
        
        # Add extraction logs
        for msg in log_msgs:
            add_log(msg)
        
        # Update session state
        st.session_state.extracted_text = extracted_text
        st.session_state.extraction_time = elapsed_time
        st.session_state.ocr_used = ocr_used
        
        # Update progress
        progress_bar.progress(100)
        status_text.text("Processing complete!")
        
        # Set status based on extraction result
        if extracted_text.strip():
            st.session_state.extraction_status = "Success"
            add_log(f"Text extraction completed in {elapsed_time:.2f} seconds")
        else:
            st.session_state.extraction_status = "Warning"
            add_log("No text was extracted from the document", level="warning")
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
    except Exception as e:
        # Handle errors
        st.session_state.extraction_status = "Error"
        add_log(f"Error extracting text: {str(e)}", level="error")
        progress_bar.progress(100)
        status_text.text("Error during processing!")

# Display the extraction results
if st.session_state.extraction_status:
    st.divider()
    
    # Header with file info and status
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.session_state.extraction_status == "Success":
            st.success("Text extracted successfully")
        elif st.session_state.extraction_status == "Warning":
            st.warning("Extraction completed with warnings")
        elif st.session_state.extraction_status == "Error":
            st.error("Text extraction failed")
        else:
            st.info(st.session_state.extraction_status)
    
    with col2:
        if st.session_state.file_name:
            st.text(f"File: {st.session_state.file_name}")
    
    with col3:
        if st.session_state.extraction_time:
            st.text(f"Time: {st.session_state.extraction_time:.2f} seconds")
    
    # Display extracted text if available
    if st.session_state.extraction_status in ["Success", "Warning"] and st.session_state.extracted_text.strip():
        st.subheader("Extracted Text")
        
        # Display OCR info if applicable
        if st.session_state.ocr_used:
            st.info("OCR was used to extract text from this document")
        
        # Text area with extracted text
        text_height = min(300, max(150, len(st.session_state.extracted_text.split('\n')) * 20))
        st.text_area(
            "Extracted content:", 
            st.session_state.extracted_text, 
            height=text_height
        )
        
        # Export options
        st.subheader("Export Options")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            if st.button("Export as TXT", use_container_width=True):
                txt_data = export_text(st.session_state.extracted_text, "txt")
                st.download_button(
                    label="Download TXT",
                    data=txt_data,
                    file_name=f"{os.path.splitext(st.session_state.file_name)[0]}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        with export_col2:
            if st.button("Export as CSV", use_container_width=True):
                csv_data = export_text(st.session_state.extracted_text, "csv")
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"{os.path.splitext(st.session_state.file_name)[0]}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with export_col3:
            if st.button("Export as JSON", use_container_width=True):
                json_data = export_text(st.session_state.extracted_text, "json")
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"{os.path.splitext(st.session_state.file_name)[0]}.json",
                    mime="application/json",
                    use_container_width=True
                )
    
    # Processing logs
    if st.session_state.log_messages:
        with st.expander("Processing Logs", expanded=False):
            log_container = st.container()
            with log_container:
                for log in st.session_state.log_messages:
                    timestamp = log["timestamp"]
                    message = log["message"]
                    level = log["level"]
                    
                    if level == "error":
                        st.error(f"[{timestamp}] {message}")
                    elif level == "warning":
                        st.warning(f"[{timestamp}] {message}")
                    else:
                        st.info(f"[{timestamp}] {message}")

# Add footer
st.divider()
st.markdown("""
<div style="text-align: center; opacity: 0.7; font-size: 0.8em;">
    Document Text Extraction Tool - For internal organizational use
</div>
""", unsafe_allow_html=True)
