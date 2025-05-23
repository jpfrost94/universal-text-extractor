"""
Data retention and export features for the Text Extraction application.
These functions help manage data lifecycle and allow users to control their data.
"""

import os
import json
import datetime
import csv
import io
import sqlite3
from pathlib import Path

# Database file
DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "text_extractor.db")

def get_db_connection():
    """
    Create a connection to the SQLite database
    
    Returns:
        SQLite connection object
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_data_older_than(days, data_type="extraction_logs"):
    """
    Get data that is older than the specified number of days
    
    Args:
        days: Number of days
        data_type: Type of data ('extraction_logs' or 'user_feedback')
        
    Returns:
        List of data rows
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the cutoff date
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        if data_type == "extraction_logs":
            cursor.execute(
                "SELECT * FROM extraction_logs WHERE timestamp < ?",
                (cutoff_date,)
            )
        elif data_type == "user_feedback":
            cursor.execute(
                "SELECT * FROM user_feedback WHERE timestamp < ?",
                (cutoff_date,)
            )
        else:
            conn.close()
            return []
        
        # Convert rows to dictionaries
        columns = [col[0] for col in cursor.description]
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
        
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting data older than {days} days: {e}")
        return []

def cleanup_old_data(days, data_type="extraction_logs"):
    """
    Remove data that is older than the specified number of days
    
    Args:
        days: Number of days
        data_type: Type of data ('extraction_logs' or 'user_feedback')
        
    Returns:
        Number of rows deleted
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the cutoff date
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        if data_type == "extraction_logs":
            cursor.execute(
                "DELETE FROM extraction_logs WHERE timestamp < ?",
                (cutoff_date,)
            )
        elif data_type == "user_feedback":
            cursor.execute(
                "DELETE FROM user_feedback WHERE timestamp < ?",
                (cutoff_date,)
            )
        else:
            conn.close()
            return 0
        
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_deleted
    except Exception as e:
        print(f"Error cleaning up data older than {days} days: {e}")
        return 0

def export_user_data(username, format_type="json", data_types=None):
    """
    Export user data in the specified format
    
    Args:
        username: Username of the user
        format_type: Export format ('json', 'csv', 'txt')
        data_types: List of data types to export ('extraction_logs', 'feedback', 'all')
        
    Returns:
        String with exported data in the specified format
    """
    if data_types is None:
        data_types = ["all"]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        result = {"username": username, "export_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        # Get extraction logs
        if "all" in data_types or "extraction_logs" in data_types:
            cursor.execute(
                "SELECT * FROM extraction_logs WHERE user_id = ? ORDER BY timestamp DESC",
                (username,)
            )
            columns = [col[0] for col in cursor.description]
            extraction_logs = []
            for row in cursor.fetchall():
                extraction_logs.append(dict(zip(columns, row)))
            result["extraction_logs"] = extraction_logs
        
        # Get user feedback
        if "all" in data_types or "feedback" in data_types:
            cursor.execute(
                "SELECT * FROM user_feedback WHERE username = ? ORDER BY timestamp DESC",
                (username,)
            )
            columns = [col[0] for col in cursor.description]
            feedback = []
            for row in cursor.fetchall():
                feedback.append(dict(zip(columns, row)))
            result["feedback"] = feedback
        
        conn.close()
        
        # Format the result according to the specified format
        if format_type == "json":
            return json.dumps(result, indent=2, default=str)
        elif format_type == "csv":
            output = io.StringIO()
            if "all" in data_types or "extraction_logs" in data_types:
                if result.get("extraction_logs") and result["extraction_logs"]:
                    output.write("EXTRACTION LOGS\n")
                    writer = csv.DictWriter(output, fieldnames=result["extraction_logs"][0].keys() if result["extraction_logs"] else [])
                    if result["extraction_logs"]:
                        writer.writeheader()
                        writer.writerows(result["extraction_logs"])
                    output.write("\n")
            
            if "all" in data_types or "feedback" in data_types:
                if result.get("feedback") and result["feedback"]:
                    output.write("USER FEEDBACK\n")
                    writer = csv.DictWriter(output, fieldnames=result["feedback"][0].keys() if result["feedback"] else [])
                    if result["feedback"]:
                        writer.writeheader()
                        writer.writerows(result["feedback"])
            
            return output.getvalue()
        elif format_type == "txt":
            output = []
            output.append(f"Data Export for User: {username}")
            output.append(f"Date: {result['export_date']}")
            output.append("")
            
            if "all" in data_types or "extraction_logs" in data_types:
                if result.get("extraction_logs") and result["extraction_logs"]:
                    output.append("=== EXTRACTION LOGS ===")
                    for log in result["extraction_logs"]:
                        output.append("-" * 40)
                        for key, value in log.items():
                            output.append(f"{key}: {value}")
                    output.append("")
            
            if "all" in data_types or "feedback" in data_types:
                if result.get("feedback") and result["feedback"]:
                    output.append("=== USER FEEDBACK ===")
                    for fb in result["feedback"]:
                        output.append("-" * 40)
                        for key, value in fb.items():
                            output.append(f"{key}: {value}")
            
            return "\n".join(output)
        else:
            return "Unsupported export format"
    except Exception as e:
        print(f"Error exporting user data: {e}")
        return f"Error exporting data: {str(e)}"