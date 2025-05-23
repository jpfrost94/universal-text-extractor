import os
import json
import datetime
import csv
from collections import defaultdict, Counter

# File to store analytics data
ANALYTICS_FILE = "usage_statistics.json"
CSV_EXPORT_FILE = "usage_statistics.csv"

def initialize_analytics():
    """
    Initialize analytics storage if it doesn't exist
    """
    if not os.path.exists(ANALYTICS_FILE):
        analytics_data = {
            "total_files_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "file_types": {},
            "file_sizes": {
                "0-1MB": 0,
                "1-5MB": 0,
                "5-10MB": 0,
                "10MB+": 0
            },
            "ocr_usage": 0,
            "avg_processing_time": 0,
            "users": {},
            "processing_dates": {},
            "daily_usage": {},
            "created_at": datetime.datetime.now().isoformat()
        }
        save_analytics(analytics_data)
        return analytics_data
    
    with open(ANALYTICS_FILE, 'r') as f:
        return json.load(f)

def save_analytics(analytics_data):
    """
    Save analytics data to file
    """
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(analytics_data, f, indent=2)

def log_extraction_event(
        file_name, 
        file_type, 
        file_size_bytes, 
        processing_time, 
        success, 
        ocr_used=False, 
        user_id="anonymous"
    ):
    """
    Log a text extraction event
    
    Args:
        file_name: Name of the processed file (stored only for file type analysis)
        file_type: Type of file processed
        file_size_bytes: Size of file in bytes
        processing_time: Time taken to process in seconds
        success: Whether extraction was successful
        ocr_used: Whether OCR was used
        user_id: Identifier for the user (if authentication is implemented)
    """
    try:
        # Load existing analytics
        try:
            analytics_data = initialize_analytics()
        except Exception as e:
            print(f"Error initializing analytics: {e}")
            return
        
        # Update total counts
        analytics_data["total_files_processed"] += 1
        
        if success:
            analytics_data["successful_extractions"] += 1
        else:
            analytics_data["failed_extractions"] += 1
        
        # Update file type statistics
        if file_type not in analytics_data["file_types"]:
            analytics_data["file_types"][file_type] = 0
        analytics_data["file_types"][file_type] += 1
        
        # Update file size statistics
        size_mb = file_size_bytes / (1024 * 1024)
        if size_mb <= 1:
            analytics_data["file_sizes"]["0-1MB"] += 1
        elif size_mb <= 5:
            analytics_data["file_sizes"]["1-5MB"] += 1
        elif size_mb <= 10:
            analytics_data["file_sizes"]["5-10MB"] += 1
        else:
            analytics_data["file_sizes"]["10MB+"] += 1
        
        # Update OCR usage
        if ocr_used:
            analytics_data["ocr_usage"] += 1
        
        # Update average processing time
        current_avg = analytics_data["avg_processing_time"]
        current_count = analytics_data["total_files_processed"]
        analytics_data["avg_processing_time"] = (
            (current_avg * (current_count - 1) + processing_time) / current_count
        )
        
        # Update user statistics
        if user_id not in analytics_data["users"]:
            analytics_data["users"][user_id] = 0
        analytics_data["users"][user_id] += 1
        
        # Update date statistics
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if today not in analytics_data["processing_dates"]:
            analytics_data["processing_dates"][today] = 0
        analytics_data["processing_dates"][today] += 1
        
        # Update daily usage
        if today not in analytics_data["daily_usage"]:
            analytics_data["daily_usage"][today] = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "types": {},
                "ocr_used": 0
            }
        
        analytics_data["daily_usage"][today]["total"] += 1
        if success:
            analytics_data["daily_usage"][today]["successful"] += 1
        else:
            analytics_data["daily_usage"][today]["failed"] += 1
        
        if file_type not in analytics_data["daily_usage"][today]["types"]:
            analytics_data["daily_usage"][today]["types"][file_type] = 0
        analytics_data["daily_usage"][today]["types"][file_type] += 1
        
        if ocr_used:
            analytics_data["daily_usage"][today]["ocr_used"] += 1
        
        # Save updated analytics
        save_analytics(analytics_data)
        
        # Also update the CSV export for easier analysis
        export_analytics_to_csv()
        
    except Exception as e:
        print(f"Error logging analytics event: {e}")

def get_analytics_summary():
    """
    Get a summary of usage statistics for display
    
    Returns:
        Dictionary with summary statistics
    """
    try:
        analytics_data = initialize_analytics()
        
        # Get top file types
        file_types = analytics_data["file_types"]
        top_file_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Get usage over time (last 7 days)
        today = datetime.datetime.now().date()
        last_week = [
            (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") 
            for i in range(7)
        ]
        last_week.reverse()  # Oldest first
        
        usage_trend = []
        for day in last_week:
            if day in analytics_data["processing_dates"]:
                usage_trend.append(analytics_data["processing_dates"][day])
            else:
                usage_trend.append(0)
        
        # Get top users
        users = analytics_data["users"]
        top_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Prepare summary
        summary = {
            "total_files_processed": analytics_data["total_files_processed"],
            "successful_rate": (
                analytics_data["successful_extractions"] / 
                analytics_data["total_files_processed"] * 100
                if analytics_data["total_files_processed"] > 0 else 0
            ),
            "top_file_types": top_file_types,
            "file_sizes": analytics_data["file_sizes"],
            "ocr_usage_rate": (
                analytics_data["ocr_usage"] / 
                analytics_data["total_files_processed"] * 100
                if analytics_data["total_files_processed"] > 0 else 0
            ),
            "avg_processing_time": analytics_data["avg_processing_time"],
            "top_users": top_users,
            "usage_trend": {
                "days": last_week,
                "counts": usage_trend
            }
        }
        
        return summary
    
    except Exception as e:
        print(f"Error getting analytics summary: {e}")
        return {
            "error": str(e),
            "total_files_processed": 0
        }

def export_analytics_to_csv():
    """
    Export analytics data to CSV for easier analysis in spreadsheet software
    """
    try:
        analytics_data = initialize_analytics()
        
        # Prepare daily data for CSV
        csv_data = []
        for date, count in analytics_data["processing_dates"].items():
            # Look up the daily usage details
            daily_data = analytics_data["daily_usage"].get(date, {})
            successful = daily_data.get("successful", 0)
            failed = daily_data.get("failed", 0)
            ocr_used = daily_data.get("ocr_used", 0)
            
            # Get file type breakdown
            file_types = daily_data.get("types", {})
            file_types_str = ", ".join([f"{k}: {v}" for k, v in file_types.items()])
            
            csv_data.append([
                date, 
                count, 
                successful, 
                failed, 
                ocr_used,
                file_types_str
            ])
        
        # Sort by date
        csv_data.sort(key=lambda x: x[0])
        
        # Write to CSV
        with open(CSV_EXPORT_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Total Files", "Successful", "Failed", "OCR Used", "File Types"])
            writer.writerows(csv_data)
            
    except Exception as e:
        print(f"Error exporting analytics to CSV: {e}")

def reset_analytics():
    """
    Reset all analytics data
    """
    try:
        if os.path.exists(ANALYTICS_FILE):
            os.remove(ANALYTICS_FILE)
        if os.path.exists(CSV_EXPORT_FILE):
            os.remove(CSV_EXPORT_FILE)
        initialize_analytics()
    except Exception as e:
        print(f"Error resetting analytics: {e}")