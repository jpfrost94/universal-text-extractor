import csv
import json
from io import StringIO
import datetime

def export_text(text, format_type):
    """
    Export extracted text to various formats.
    
    Args:
        text: The extracted text
        format_type: The export format (txt, csv, json)
    
    Returns:
        String data in the requested format
    """
    if format_type == "txt":
        return text
    
    elif format_type == "csv":
        # Create a CSV with one column for the extracted text
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Extracted Text"])
        
        # Write text content, line by line
        for line in text.split('\n'):
            writer.writerow([line])
        
        return output.getvalue()
    
    elif format_type == "json":
        # Create a JSON object
        data = {
            "extracted_text": text,
            "extraction_timestamp": datetime.datetime.now().isoformat(),
            "lines": text.split('\n')
        }
        
        return json.dumps(data, indent=2)
    
    else:
        # Default fallback
        return text
