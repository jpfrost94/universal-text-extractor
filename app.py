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
from utils.database import (
    get_analytics_summary, log_extraction_event, reset_analytics,
    get_user_by_username as db_get_user
)
# We now have data management functions directly in the database module
from utils.database import (
    get_data_older_than, cleanup_old_data, export_user_data
)
from utils.auth_db import (
    authenticate_user, is_admin, add_user, change_password,
    initialize_users, ROLE_ADMIN, ROLE_USER
)

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
    
# Authentication state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Initialize authentication system
initialize_users()

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

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

# Analytics are now initialized by the database module

# Login function
def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username", key="login_username")
    password = st.sidebar.text_input("Password", type="password", key="login_password")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("Login", key="login_button"):
            user = authenticate_user(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.is_admin = is_admin(username)
                st.sidebar.success(f"Logged in as {username}")
                
                # Force page reload to update UI
                st.rerun()
            else:
                st.sidebar.error("Invalid username or password")
    
    with col2:
        if st.button("Register", key="show_register_button"):
            st.session_state.show_registration = True
            st.rerun()

# Registration function
def register():
    st.sidebar.title("Register New Account")
    
    username = st.sidebar.text_input("Choose Username", key="reg_username")
    password = st.sidebar.text_input("Choose Password", type="password", key="reg_password")
    confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="reg_confirm")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("Create Account", key="register_button"):
            # Validate inputs
            if not username or not password:
                st.sidebar.error("Username and password are required")
            elif password != confirm_password:
                st.sidebar.error("Passwords do not match")
            elif len(password) < 6:
                st.sidebar.error("Password must be at least 6 characters")
            else:
                # Attempt to create the account
                if add_user(username, password, ROLE_USER):
                    st.sidebar.success(f"Account created for {username}. You can now log in.")
                    # Reset the registration flag and return to login
                    st.session_state.show_registration = False
                    st.rerun()
                else:
                    st.sidebar.error(f"Username '{username}' already exists")
    
    with col2:
        if st.button("Back to Login", key="back_to_login_button"):
            st.session_state.show_registration = False
            st.rerun()

# Logout function
def logout():
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.is_admin = False
        
        # Force page reload to update UI
        st.rerun()

# Initialize registration state if needed
if 'show_registration' not in st.session_state:
    st.session_state.show_registration = False

# Sidebar
with st.sidebar:
    st.title("Text Extraction Tool")
    
    # Login/logout section
    if st.session_state.authenticated:
        st.write(f"Logged in as: **{st.session_state.username}**")
        if st.session_state.is_admin:
            st.write("Role: **Administrator**")
        else:
            st.write("Role: **User**")
        logout()
    else:
        if st.session_state.show_registration:
            register()
        else:
            login()
    
    # Navigation
    if st.session_state.authenticated:
        if st.session_state.is_admin:
            page = st.radio("Navigation", ["Text Extraction", "Usage Statistics", "Admin Panel"])
        else:
            page = st.radio("Navigation", ["Text Extraction", "My Statistics", "Feedback"])
    else:
        page = "Text Extraction"
    
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

# Define user feedback storage if it doesn't exist
if 'user_feedback' not in st.session_state:
    st.session_state.user_feedback = {}

# Main content based on selected page
if page == "Text Extraction":
    # Text Extraction UI
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
elif page == "Usage Statistics":
    st.title("Usage Statistics")
    
    # Check if user is authenticated and is an admin
    if not st.session_state.authenticated:
        st.warning("You need to log in to access this page.")
        st.info("Please log in using the sidebar.")
    elif not st.session_state.is_admin:
        st.error("You don't have permission to access the usage statistics.")
        st.info("This page is only accessible to administrators.")
    else:
        # Display the analytics dashboard for admins
        st.success("Viewing statistics as administrator")
        st.write("This page shows anonymous usage statistics about how the text extraction tool is being used.")
        
        # Get statistics summary
        stats = get_analytics_summary()
        
        # Display key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Files Processed", stats["total_files_processed"])
        
        with col2:
            success_rate = f"{stats['successful_rate']:.1f}%"
            st.metric("Success Rate", success_rate)
        
        with col3:
            ocr_rate = f"{stats['ocr_usage_rate']:.1f}%"
            st.metric("OCR Usage", ocr_rate)
        
        # File Type Analysis
        st.subheader("File Type Analysis")
        
        if stats["top_file_types"]:
            # Create data for a chart
            labels = [f".{ft}" for ft, _ in stats["top_file_types"]]
            values = [count for _, count in stats["top_file_types"]]
            
            # Display as a table for now (could be a chart in a real implementation)
            file_type_data = {"File Type": labels, "Count": values}
            st.table(file_type_data)
        else:
            st.info("No file type data available yet.")
        
        # File Size Distribution
        st.subheader("File Size Distribution")
        
        file_sizes = stats["file_sizes"]
        if sum(file_sizes.values()) > 0:
            # Display as a table
            size_data = {"Size Range": list(file_sizes.keys()), "Count": list(file_sizes.values())}
            st.table(size_data)
        else:
            st.info("No file size data available yet.")
        
        # Usage Trend
        st.subheader("Usage Trend (Last 7 Days)")
        
        trend_data = {"Date": stats["usage_trend"]["days"], "Files Processed": stats["usage_trend"]["counts"]}
        st.line_chart(trend_data, x="Date")
        
        # Top Users (if tracking is enabled)
        if stats["top_users"] and stats["top_users"][0][0] != "anonymous":
            st.subheader("Top Users")
            user_data = {"User": [u for u, _ in stats["top_users"]], "Files Processed": [c for _, c in stats["top_users"]]}
            st.table(user_data)
        
        # Admin controls
        st.divider()
        
        # Statistics management
        st.subheader("Statistics Management")
        if st.button("Reset Statistics", type="secondary"):
            reset_analytics()
            st.success("Usage statistics have been reset.")
            st.rerun()
        
        # Download CSV option
        if os.path.exists("usage_statistics.csv"):
            with open("usage_statistics.csv", "rb") as file:
                st.download_button(
                    label="Download Statistics as CSV",
                    data=file,
                    file_name="text_extractor_statistics.csv",
                    mime="text/csv"
                )
        
        # User Management section
        st.subheader("User Management")
        
        # Add new user form
        with st.expander("Add New User", expanded=False):
            new_username = st.text_input("New Username", key="new_username")
            new_password = st.text_input("New Password", type="password", key="new_password")
            is_new_admin = st.checkbox("Admin Access", value=False, key="is_new_admin")
            
            if st.button("Add User"):
                if new_username and new_password:
                    role = ROLE_ADMIN if is_new_admin else "user"
                    if add_user(new_username, new_password, role):
                        st.success(f"User '{new_username}' added successfully.")
                    else:
                        st.error(f"User '{new_username}' already exists.")
                else:
                    st.warning("Username and password are required.")
else:
    # File uploader (fallback if the navigation somehow fails)
    uploaded_file = st.file_uploader(
        "Upload a document to extract text", 
        type=sum(SUPPORTED_FILE_TYPES.values(), []),
        help="Upload a file to extract text from it."
    )

# Only show advanced options if a file is uploaded
if 'uploaded_file' in locals() and uploaded_file is not None:
    # OCR and image processing options
    show_advanced = st.checkbox("Show advanced options", value=False)
    
    # Advanced options UI
    if show_advanced:
        # Default values
        use_ocr = False
        ocr_language = "eng"
        enhance_image = False
        grayscale = False
        contrast_enhancement = 1.0
        threshold_value = 128
        noise_reduction = False
    
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
else:
    # Default values when no file is uploaded
    show_advanced = False
    use_ocr = False
    ocr_language = "eng"
    enhance_image = False
    grayscale = False
    contrast_enhancement = 1.0
    threshold_value = 128
    noise_reduction = False

# Process Button (only show on Text Extraction page)
process_clicked = False
if page == "Text Extraction":
    process_clicked = st.button("Process Document", type="primary", use_container_width=True)

# Process the file when button is clicked
if process_clicked and 'uploaded_file' in locals() and uploaded_file is not None:
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
        success = False
        if extracted_text.strip():
            st.session_state.extraction_status = "Success"
            add_log(f"Text extraction completed in {elapsed_time:.2f} seconds")
            success = True
        else:
            st.session_state.extraction_status = "Warning"
            add_log("No text was extracted from the document", level="warning")
        
        # Record analytics for this extraction
        # Get the file size in bytes
        file_size = len(uploaded_file.getvalue())
        
        # Log the extraction event
        log_extraction_event(
            user_id=st.session_state.username if st.session_state.authenticated else "anonymous",
            file_name=uploaded_file.name,
            file_type=file_type,
            file_size_bytes=file_size,
            processing_time=elapsed_time,
            success=success,
            ocr_used=ocr_used
        )
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
    except Exception as e:
        # Handle errors
        st.session_state.extraction_status = "Error"
        add_log(f"Error extracting text: {str(e)}", level="error")
        progress_bar.progress(100)
        status_text.text("Error during processing!")
        
        # Log the error in analytics
        try:
            # Get the file size in bytes
            file_size = len(uploaded_file.getvalue())
            
            # Log the failed extraction event
            log_extraction_event(
                file_name=uploaded_file.name,
                file_type=getattr(st.session_state, 'file_type', 'unknown'),
                file_size_bytes=file_size,
                processing_time=0.0,
                success=False,
                ocr_used=False,
                user_id="anonymous"
            )
        except Exception as analytics_error:
            add_log(f"Error logging analytics: {str(analytics_error)}", level="error")

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

# User Statistics page
elif page == "My Statistics":
    if st.session_state.authenticated and not st.session_state.is_admin:
        st.title("My Statistics")
        
        username = st.session_state.username
        
        # Get user-specific statistics from the database
        stats = get_analytics_summary(username)
        
        # Create tabs for different views
        stats_tabs = st.tabs(["Overview", "Data Management", "Export Options"])
        
        with stats_tabs[0]:
            # Display user-specific stats
            st.subheader("Your Document Processing History")
            
            # User total processed
            user_total = stats["total_processed"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Your Files Processed", user_total)
            with col2:
                st.metric("Successful Extractions", int(user_total * stats.get("success_rate", 0) / 100))
            with col3:
                st.metric("OCR Used", int(user_total * stats.get("ocr_usage", 0) / 100))
            
            # Display usage trend
            if stats["usage_trend"]["days"]:
                st.subheader("Your Usage Over Time")
                trend_data = {"Date": stats["usage_trend"]["days"], "Files Processed": stats["usage_trend"]["counts"]}
                st.line_chart(trend_data, x="Date")
            
            # Display file type distribution
            if stats["top_file_types"]:
                st.subheader("File Types Processed")
                file_type_data = {
                    "File Type": [ft for ft, _ in stats["top_file_types"]],
                    "Count": [count for _, count in stats["top_file_types"]]
                }
                st.bar_chart(file_type_data, x="File Type")
            
            # Tips for better extraction results
            st.subheader("Tips for Better Results")
            st.markdown("""
            - For scanned documents, enable OCR processing
            - Try image preprocessing for better OCR results
            - For PDFs with embedded text, disable OCR to speed up processing
            - Large files may take longer to process
            """)
            
        with stats_tabs[1]:
            st.subheader("Data Retention Policy")
            
            # Display data retention information
            st.info("""
            To optimize storage space, your extraction data is kept for a limited time:
            - Text extraction history: 90 days
            - Feedback submissions: 1 year
            
            You can export your data at any time before it expires.
            """)
            
            # Show expiring data count
            expiring_extractions = len(get_data_older_than(60, "extraction_logs"))
            if expiring_extractions > 0:
                st.warning(f"You have {expiring_extractions} extraction records that will expire soon. Consider exporting your data.")
            
            # Option to manually clean up data
            st.subheader("Data Cleanup")
            cleanup_days = st.slider("Delete data older than (days)", min_value=30, max_value=365, value=90, step=30)
            
            if st.button("Clean Up Old Data"):
                deleted_count = cleanup_old_data(cleanup_days, "extraction_logs")
                st.success(f"Removed {deleted_count} old extraction records.")
                st.rerun()
            
        with stats_tabs[2]:
            st.subheader("Export Your Data")
            
            # Export options
            st.write("Export your extraction history and feedback in different formats.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.selectbox(
                    "Select Export Format", 
                    ["JSON", "CSV", "TXT"],
                    help="JSON is best for technical uses, CSV for spreadsheets, TXT for easy reading."
                )
            
            with col2:
                export_data = st.multiselect(
                    "Data to Include",
                    ["Extraction History", "Feedback"],
                    default=["Extraction History"],
                    help="Select what data to include in your export"
                )
            
            # Map the selected options to the actual parameter values
            format_map = {"JSON": "json", "CSV": "csv", "TXT": "txt"}
            data_map = {
                "Extraction History": "extraction_logs", 
                "Feedback": "feedback"
            }
            
            format_type = format_map[export_format]
            data_types = [data_map[d] for d in export_data]
            
            if st.button("Generate Export"):
                export_data_result = export_user_data(username, format_type, data_types)
                
                if format_type == "json":
                    mime_type = "application/json"
                    file_ext = "json"
                elif format_type == "csv":
                    mime_type = "text/csv"
                    file_ext = "csv"
                else:
                    mime_type = "text/plain"
                    file_ext = "txt"
                
                # Allow user to download the export
                st.download_button(
                    label="Download Export",
                    data=export_data_result,
                    file_name=f"text_extractor_data_{username}_{datetime.now().strftime('%Y%m%d')}.{file_ext}",
                    mime=mime_type
                )
                
                st.success("Export generated successfully! Click the download button to save it.")
                
            st.info("Data exports contain only your personal data and statistics. The system automatically removes data older than the retention period to save space.")

# User Feedback page
elif page == "Feedback":
    if st.session_state.authenticated and not st.session_state.is_admin:
        st.title("Provide Feedback")
        
        # Get the current username
        current_username = st.session_state.username
        
        # Feedback form
        with st.form("feedback_form"):
            st.write("We value your feedback on the Text Extraction Tool")
            
            feedback_type = st.selectbox(
                "Feedback Type",
                ["General Feedback", "Bug Report", "Feature Request", "Usability Issue"]
            )
            
            feedback_text = st.text_area(
                "Your Feedback",
                height=150,
                placeholder="Please describe your experience, issue, or suggestion..."
            )
            
            rating = st.slider(
                "Rate your experience with the tool",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Poor, 5 = Excellent"
            )
            
            submit_button = st.form_submit_button("Submit Feedback")
            
            if submit_button and feedback_text:
                # Save feedback to the database
                from utils.database import save_user_feedback
                if save_user_feedback(current_username, feedback_type, feedback_text, rating):
                    st.success("Thank you for your feedback! We'll use it to improve the tool.")
                else:
                    st.error("There was a problem saving your feedback. Please try again.")
            elif submit_button:
                st.warning("Please provide your feedback before submitting.")
        
        # Display previous feedback from this user
        from utils.database import get_user_feedback
        user_feedback_list = get_user_feedback(current_username)
        
        if user_feedback_list:
            st.subheader("Your Previous Feedback")
            for i, fb in enumerate(user_feedback_list):
                with st.expander(f"Feedback #{i+1} - {fb['timestamp']}"):
                    st.write(f"**Type:** {fb['type']}")
                    st.write(f"**Rating:** {'⭐' * fb['rating']}")
                    st.write(f"**Feedback:** {fb['text']}")

# Admin Panel page
elif page == "Admin Panel":
    if st.session_state.authenticated and st.session_state.is_admin:
        st.title("Admin Panel")
        
        admin_tabs = st.tabs(["User Management", "Feedback Management", "System Settings"])
        
        with admin_tabs[0]:
            st.subheader("User Management")
            
            # Add new user form
            with st.expander("Add New User", expanded=False):
                new_username = st.text_input("New Username", key="new_username")
                new_password = st.text_input("New Password", type="password", key="new_password")
                is_new_admin = st.checkbox("Admin Access", value=False, key="is_new_admin")
                
                if st.button("Add User"):
                    if new_username and new_password:
                        role = ROLE_ADMIN if is_new_admin else ROLE_USER
                        if add_user(new_username, new_password, role):
                            st.success(f"User '{new_username}' added successfully.")
                        else:
                            st.error(f"User '{new_username}' already exists.")
                    else:
                        st.warning("Username and password are required.")
        
        with admin_tabs[1]:
            st.subheader("User Feedback")
            
            # Display all feedback from users using the database
            from utils.database import get_user_feedback
            all_feedback = get_user_feedback()
            
            if all_feedback:
                # Group feedback by username
                feedback_by_user = {}
                for fb in all_feedback:
                    username = fb['username']
                    if username not in feedback_by_user:
                        feedback_by_user[username] = []
                    feedback_by_user[username].append(fb)
                
                # Display feedback grouped by user
                for username, feedbacks in feedback_by_user.items():
                    st.subheader(f"Feedback from {username}")
                    for i, fb in enumerate(feedbacks):
                        with st.expander(f"{fb['type']} - {fb['timestamp']}"):
                            st.write(f"**Rating:** {'⭐' * fb['rating']}")
                            st.write(f"**Feedback:** {fb['text']}")
            else:
                st.info("No feedback has been submitted yet.")
        
        with admin_tabs[2]:
            st.subheader("System Settings")
            
            # OCR Settings
            st.write("OCR Settings")
            st.warning("OCR settings management will be implemented in a future update.")
            
            # Reset Statistics
            st.write("Statistics Management")
            if st.button("Reset All Statistics", type="secondary"):
                reset_analytics()
                st.success("Usage statistics have been reset.")
                st.rerun()

# Add footer
st.divider()
st.markdown("""
<div style="text-align: center; opacity: 0.7; font-size: 0.8em;">
    Document Text Extraction Tool - For internal organizational use
</div>
""", unsafe_allow_html=True)
