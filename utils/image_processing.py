import os
import tempfile
from io import BytesIO

# Try to import image processing libraries
try:
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
    has_pil = True
except ImportError:
    has_pil = False
    Image, ImageOps, ImageFilter, ImageEnhance = None, None, None, None

# Try to import HEIC/HEIF support
try:
    import pillow_heif
    has_heif_support = True
    pillow_heif.register_heif_opener()
except ImportError:
    pillow_heif = None
    has_heif_support = False

# Try to import OpenCV
try:
    import cv2
    import numpy as np
    has_opencv = True
except ImportError:
    has_opencv = False
    cv2, np = None, None

def preprocess_image(image_path, params=None):
    """
    Preprocess an image for better OCR results.
    
    Args:
        image_path: Path to image file or PIL Image object
        params: Dictionary of preprocessing parameters:
            - enhance: Whether to enhance the image
            - grayscale: Whether to convert to grayscale
            - contrast: Contrast adjustment factor
            - threshold: Threshold value for binarization
            - noise_reduction: Whether to apply noise reduction
    
    Returns:
        Processed PIL Image object or the image path if PIL is not available
    """
    if not has_pil:
        # Return the original path if PIL is not available
        return image_path
    
    # Set default parameters if not provided
    if params is None:
        params = {
            "enhance": True,
            "grayscale": True,
            "contrast": 1.5,
            "threshold": 130,
            "noise_reduction": True
        }
    
    # If input is a path, open the image
    if isinstance(image_path, str):
        # Handle HEIC/HEIF files if support is available
        if (image_path.lower().endswith(('.heic', '.heif')) and has_heif_support):
            try:
                img = Image.open(image_path)
            except Exception as e:
                # Log and return original path on error
                print(f"Error opening HEIC/HEIF image: {e}")
                return image_path
        else:
            # Open regular image types
            try:
                img = Image.open(image_path)
            except Exception as e:
                # Log and return original path on error
                print(f"Error opening image: {e}")
                return image_path
    else:
        # Use the provided image object
        img = image_path
    
    # Apply image processing steps if enhance is enabled
    if params.get("enhance", True):
        # Convert to RGB mode if not already
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 1. Convert to grayscale if requested
        if params.get("grayscale", True):
            img = ImageOps.grayscale(img)
        
        # 2. Adjust contrast if specified
        contrast_factor = params.get("contrast", 1.5)
        if contrast_factor != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast_factor)
        
        # 3. Apply threshold if in grayscale mode
        if params.get("grayscale", True) and params.get("threshold", None):
            # Convert to binary using threshold
            threshold_value = params.get("threshold", 130)
            img = img.point(lambda p: 255 if p > threshold_value else 0)
        
        # 4. Apply noise reduction if requested
        if params.get("noise_reduction", True):
            # Apply median filter to reduce noise
            img = img.filter(ImageFilter.MedianFilter(size=3))
    
    # If OpenCV is available and we have advanced options, use it for additional processing
    if has_opencv and params.get("use_opencv", False):
        try:
            # Convert PIL image to OpenCV format
            img_array = np.array(img)
            
            # Apply advanced OpenCV processing here if needed
            # Example: adaptive thresholding
            if len(img_array.shape) == 2:  # Grayscale
                img_cv = cv2.adaptiveThreshold(
                    img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
                # Convert back to PIL
                img = Image.fromarray(img_cv)
        except Exception as e:
            # Log error but continue with PIL-processed image
            print(f"OpenCV processing failed: {e}")
    
    # Save to a temporary file if needed by OCR engines
    if params.get("save_temp", False):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            img.save(tmp_file.name)
            return tmp_file.name
    
    return img

def is_image_scanned_document(image_path):
    """
    Check if an image is likely a scanned document.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Boolean indicating if image appears to be a scanned document
    """
    if not has_pil:
        return False
    
    try:
        # Open image
        img = Image.open(image_path)
        
        # Convert to grayscale for analysis
        img_gray = img.convert('L')
        
        # Simple heuristics to identify scanned documents:
        # 1. Check image dimensions (typical document sizes)
        width, height = img.size
        aspect_ratio = width / height
        
        # Most documents have aspect ratios close to standard paper sizes
        is_document_size = 0.65 <= aspect_ratio <= 0.75 or 1.3 <= aspect_ratio <= 1.55
        
        # 2. Check for predominant white background
        histogram = img_gray.histogram()
        total_pixels = width * height
        white_pixels = sum(histogram[200:])  # Count pixels with brightness > 200
        white_percentage = white_pixels / total_pixels
        
        has_white_background = white_percentage > 0.7  # More than 70% is white
        
        # 3. Use edge detection for text regions if OpenCV is available
        has_text_regions = False
        if has_opencv:
            # Convert PIL image to OpenCV format
            img_cv = np.array(img_gray)
            
            # Apply edge detection
            edges = cv2.Canny(img_cv, 100, 200)
            edge_pixels = np.count_nonzero(edges)
            edge_density = edge_pixels / total_pixels
            
            # Documents typically have a moderate edge density
            has_text_regions = 0.01 <= edge_density <= 0.1
        
        # Combine criteria (adjust weights as needed)
        if has_opencv:
            return (is_document_size and has_white_background) or has_text_regions
        else:
            return is_document_size and has_white_background
    
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return False

def detect_image_orientation(image_path):
    """
    Detect if an image needs rotation for proper text orientation.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Estimated rotation angle in degrees (0, 90, 180, or 270)
    """
    # This function would ideally use OCR or ML to detect text orientation
    # A simplified version is implemented here
    
    if not has_opencv:
        return 0  # No rotation if OpenCV is not available
    
    try:
        # Open image with OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return 0
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Try all 4 orientations and see which gives the most horizontal lines
        # (This is a simple heuristic; real orientation detection is more complex)
        best_orientation = 0
        max_horizontal_lines = 0
        
        for angle in [0, 90, 180, 270]:
            if angle == 0:
                rotated = gray
            else:
                # Rotate image
                if angle == 90:
                    rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
                elif angle == 180:
                    rotated = cv2.rotate(gray, cv2.ROTATE_180)
                else:  # angle == 270
                    rotated = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            # Detect horizontal lines using Hough transform
            edges = cv2.Canny(rotated, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
            
            if lines is None:
                continue
                
            # Count horizontal lines (within 10 degrees of horizontal)
            horizontal_lines = 0
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if abs(y2 - y1) < 0.2 * abs(x2 - x1):  # Roughly horizontal
                    horizontal_lines += 1
            
            # Update best orientation if this one has more horizontal lines
            if horizontal_lines > max_horizontal_lines:
                max_horizontal_lines = horizontal_lines
                best_orientation = angle
        
        return best_orientation
    
    except Exception as e:
        print(f"Error detecting image orientation: {e}")
        return 0  # Default to no rotation
