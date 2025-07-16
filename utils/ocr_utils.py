import os
import tempfile
from io import BytesIO

# Try to import OCR libraries
try:
    import pytesseract
    has_pytesseract = True
    # For Windows, specify the Tesseract path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    has_pytesseract = False
    pytesseract = None

try:
    import easyocr
    has_easyocr = True
    # Initialize the EasyOCR reader lazily to save memory
    easyocr_reader = None
except ImportError:
    has_easyocr = False
    easyocr = None
    easyocr_reader = None

try:
    from PIL import Image
    has_pil = True
except ImportError:
    has_pil = False
    Image = None

def is_ocr_available():
    """
    Check if any OCR functionality is available.
    
    Returns:
        Boolean indicating if OCR is available
    """
    return has_pytesseract or has_easyocr

def get_available_ocr_backends():
    """
    Get list of available OCR backends.
    
    Returns:
        List of available OCR backend names
    """
    backends = []
    if has_pytesseract:
        backends.append("Tesseract")
    if has_easyocr:
        backends.append("EasyOCR")
    return backends

def get_tesseract_languages():
    """
    Get list of available Tesseract language packs.
    
    Returns:
        List of available language codes or empty list if Tesseract is not available
    """
    if not has_pytesseract:
        return []
    
    try:
        return pytesseract.get_languages(config='')
    except Exception:
        # Default to common languages if we can't get the actual list
        return ["eng"]

def initialize_easyocr(lang="en"):
    """
    Initialize the EasyOCR reader for the specified language.
    
    Args:
        lang: Language code (e.g., 'en' for English)
    
    Returns:
        EasyOCR Reader object or None if EasyOCR is not available
    """
    global easyocr_reader
    
    if not has_easyocr:
        return None
    
    # Map from standard language codes to EasyOCR language codes
    lang_map = {
        "eng": "en",
        "fra": "fr",
        "deu": "de",
        "spa": "es",
        "ita": "it",
        "por": "pt",
        "chi_sim": "ch_sim",
        "jpn": "ja",
        "kor": "ko"
    }
    
    # Convert Tesseract-style language code if needed
    if lang in lang_map:
        lang = lang_map[lang]
    
    try:
        # Only create a new reader if language changed or if it's the first time
        if easyocr_reader is None or easyocr_reader.lang_list != [lang]:
            easyocr_reader = easyocr.Reader([lang], gpu=False)
        return easyocr_reader
    except Exception as e:
        print(f"Error initializing EasyOCR: {e}")
        return None

def perform_ocr(image, language="eng", handwriting_mode=False):
    """
    Perform OCR on an image using available OCR libraries.
    
    Args:
        image: Path to image file or PIL Image object
        language: Language code for OCR
        handwriting_mode: Whether to optimize for handwriting recognition
    
    Returns:
        Extracted text as string
    """
    ocr_text = ""
    
    # Ensure we have at least one OCR library available
    if not is_ocr_available():
        return "[OCR is not available. No text could be extracted from this image.]"
    
    # Try Tesseract first if available
    if has_pytesseract:
        try:
            # Configure Tesseract for handwriting if requested
            config = ""
            if handwriting_mode:
                # PSM 6: Uniform block of text (good for handwriting)
                # PSM 8: Single word (for isolated handwritten words)
                # PSM 13: Raw line (for handwritten lines)
                config = "--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;: "
            
            if isinstance(image, str):
                # It's a file path
                if config:
                    ocr_text = pytesseract.image_to_string(Image.open(image), lang=language, config=config)
                else:
                    ocr_text = pytesseract.image_to_string(Image.open(image), lang=language)
            else:
                # It's a PIL Image object
                if config:
                    ocr_text = pytesseract.image_to_string(image, lang=language, config=config)
                else:
                    ocr_text = pytesseract.image_to_string(image, lang=language)
            
            # If we got text, return it
            if ocr_text.strip():
                return ocr_text
            
            # If handwriting mode failed, try again with different PSM
            if handwriting_mode and not ocr_text.strip():
                try:
                    config_alt = "--psm 8"  # Try single word mode
                    if isinstance(image, str):
                        ocr_text = pytesseract.image_to_string(Image.open(image), lang=language, config=config_alt)
                    else:
                        ocr_text = pytesseract.image_to_string(image, lang=language, config=config_alt)
                    
                    if ocr_text.strip():
                        return ocr_text
                except Exception:
                    pass  # Continue to EasyOCR fallback
            
            # If no text was found, the OCR process completed but didn't find text
            # or the image might be problematic, so we'll try EasyOCR as a fallback
        except Exception as e:
            print(f"Tesseract OCR failed: {e}")
            # Fall through to try EasyOCR
    
    # Try EasyOCR if Tesseract failed or isn't available
    if has_easyocr:
        try:
            # Initialize EasyOCR reader
            reader = initialize_easyocr(language)
            
            if reader:
                # Perform OCR with EasyOCR
                if isinstance(image, str):
                    # It's a file path
                    result = reader.readtext(image)
                else:
                    # It's a PIL Image object, convert to numpy array
                    if has_pil and isinstance(image, Image.Image):
                        # Save to a temporary file if PIL image
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                            image.save(tmp_file.name)
                            result = reader.readtext(tmp_file.name)
                            os.unlink(tmp_file.name)
                    else:
                        # No valid image format for EasyOCR
                        return "[Could not process image for OCR: Invalid image format]"
                
                # Extract text from results
                ocr_text = "\n".join([text for _, text, _ in result])
        except Exception as e:
            print(f"EasyOCR failed: {e}")
            if not ocr_text:
                ocr_text = f"[OCR processing failed: {str(e)}]"
    
    return ocr_text if ocr_text.strip() else "[No text was detected in this image.]"
