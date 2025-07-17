"""
Universal Text Extractor API
Simple interface for using the text extractor in Jupyter notebooks or other Python scripts
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add the current directory to Python path to import utils
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from utils.file_handlers import detect_file_type, extract_text_from_file
from utils.ocr_utils import is_ocr_available, get_available_ocr_backends
from utils.image_processing import preprocess_image


class TextExtractor:
    """
    Simple API wrapper for the Universal Text Extractor
    """
    
    def __init__(self):
        """Initialize the text extractor"""
        self.ocr_available = is_ocr_available()
        self.ocr_backends = get_available_ocr_backends()
        
    def extract_from_file(self, file_path: str, language: str = "eng", 
                         handwriting_mode: bool = False) -> Dict[str, Any]:
        """
        Extract text from a file
        
        Args:
            file_path: Path to the file
            language: OCR language code (default: "eng")
            handwriting_mode: Enable handwriting recognition mode
            
        Returns:
            Dictionary with extraction results
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "text": "",
                "file_type": None,
                "ocr_used": False
            }
        
        try:
            # Detect file type
            file_type = detect_file_type(file_path)
            
            # Extract text
            result = extract_text_from_file(
                file_path, 
                language=language,
                handwriting_mode=handwriting_mode
            )
            
            return {
                "success": True,
                "text": result["text"],
                "file_type": file_type,
                "ocr_used": result.get("ocr_used", False),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "file_type": None,
                "ocr_used": False
            }
    
    def extract_from_image(self, image_path: str, language: str = "eng",
                          handwriting_mode: bool = False, 
                          preprocess: bool = True) -> Dict[str, Any]:
        """
        Extract text from an image using OCR
        
        Args:
            image_path: Path to the image file
            language: OCR language code
            handwriting_mode: Enable handwriting recognition
            preprocess: Apply image preprocessing
            
        Returns:
            Dictionary with extraction results
        """
        if not self.ocr_available:
            return {
                "success": False,
                "error": "OCR is not available. Please install pytesseract or easyocr.",
                "text": "",
                "file_type": "image",
                "ocr_used": False
            }
        
        try:
            # Preprocess image if requested
            processed_image_path = image_path
            if preprocess:
                processed_image_path = preprocess_image(image_path)
            
            # Extract text using OCR
            from utils.ocr_utils import perform_ocr
            text = perform_ocr(processed_image_path, language, handwriting_mode)
            
            return {
                "success": True,
                "text": text,
                "file_type": "image",
                "ocr_used": True,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "file_type": "image",
                "ocr_used": False
            }
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get list of supported file formats"""
        from utils.file_handlers import SUPPORTED_FILE_TYPES, SUPPORTED_IMAGE_FORMATS
        
        return {
            "documents": list(SUPPORTED_FILE_TYPES.keys()),
            "images": SUPPORTED_IMAGE_FORMATS,
            "ocr_available": self.ocr_available,
            "ocr_backends": self.ocr_backends
        }
    
    def batch_extract(self, file_paths: list, language: str = "eng") -> Dict[str, Any]:
        """
        Extract text from multiple files
        
        Args:
            file_paths: List of file paths
            language: OCR language code
            
        Returns:
            Dictionary with results for each file
        """
        results = {}
        
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            results[filename] = self.extract_from_file(file_path, language)
        
        return results


# Convenience functions for quick use
def extract_text(file_path: str, language: str = "eng", handwriting_mode: bool = False) -> str:
    """
    Quick function to extract text from a file
    
    Args:
        file_path: Path to the file
        language: OCR language code
        handwriting_mode: Enable handwriting recognition
        
    Returns:
        Extracted text as string
    """
    extractor = TextExtractor()
    result = extractor.extract_from_file(file_path, language, handwriting_mode)
    
    if result["success"]:
        return result["text"]
    else:
        raise Exception(f"Text extraction failed: {result['error']}")


def extract_from_image(image_path: str, language: str = "eng", handwriting_mode: bool = False) -> str:
    """
    Quick function to extract text from an image
    
    Args:
        image_path: Path to the image
        language: OCR language code
        handwriting_mode: Enable handwriting recognition
        
    Returns:
        Extracted text as string
    """
    extractor = TextExtractor()
    result = extractor.extract_from_image(image_path, language, handwriting_mode)
    
    if result["success"]:
        return result["text"]
    else:
        raise Exception(f"OCR extraction failed: {result['error']}")


if __name__ == "__main__":
    # Example usage
    extractor = TextExtractor()
    print("Supported formats:", extractor.get_supported_formats())