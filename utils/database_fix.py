"""
Corrected database module with proper data retention features.
"""

import os
import sqlite3
import json
import datetime
from pathlib import Path

# Database file
DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "text_extractor.db")

# Make sure data directory exists
os.makedirs(DB_DIR, exist_ok=True)

def get_db_connection():
    """
    Create a connection to the SQLite database
    
    Returns:
        SQLite connection object
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """
    Initialize the database with required tables
    """
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        require_password_change INTEGER DEFAULT 0
    )
    ''')
    
    # Create extraction logs table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS extraction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size_bytes INTEGER NOT NULL,
        processing_time REAL NOT NULL,
        success INTEGER NOT NULL,
        ocr_used INTEGER NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create user feedback table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS user_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        feedback_type TEXT NOT NULL,
        feedback_text TEXT NOT NULL,
        rating INTEGER NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def migrate_json_to_db():
    """
    Migrate existing JSON data to the database if available
    """
    users_file = "users.json"
    
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users = json.load(f)
            
            conn = get_db_connection()
            
            for username, user_data in users.items():
                # Check if user already exists
                cursor = conn.execute("SELECT username FROM users WHERE username = ?", (username,))
                if cursor.fetchone() is None:
                    conn.execute(
                        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                        (username, user_data['password_hash'], user_data['role'])
                    )
            
            conn.commit()
            conn.close()
            
            # Rename the file to prevent re-migration
            os.rename(users_file, f"{users_file}.migrated")
            print(f"Migrated users from {users_file} to the database")
        except Exception as e:
            print(f"Error migrating users from JSON: {e}")

# User management functions
def get_user_by_username(username):
    """
    Get a user by username
    
    Args:
        username: Username
    
    Returns:
        User dict if found, None otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT username, password_hash, role, require_password_change FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None
    except Exception as e:
        print(f"Error retrieving user: {e}")
        return None

def add_user(username, password_hash, role, require_password_change=False):
    """
    Add a new user
    
    Args:
        username: Username
        password_hash: Hashed password
        role: User role
        require_password_change: Whether user must change password on next login
    
    Returns:
        True if added, False if username already exists
    """
    try:
        conn = get_db_connection()
        
        # Check if username already exists
        cursor = conn.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False
        
        conn.execute(
            "INSERT INTO users (username, password_hash, role, require_password_change) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, 1 if require_password_change else 0)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding user: {e}")
        return False

def change_password(username, new_password_hash):
    """
    Change a user's password
    
    Args:
        username: Username
        new_password_hash: New hashed password
    
    Returns:
        True if changed, False if user not found
    """
    try:
        conn = get_db_connection()
        
        # Check if user exists
        cursor = conn.execute("SELECT username FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        conn.execute(
            "UPDATE users SET password_hash = ?, require_password_change = 0 WHERE username = ?",
            (new_password_hash, username)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error changing password: {e}")
        return False

def get_all_users():
    """
    Get all users
    
    Returns:
        List of user dicts
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT username, role FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    except Exception as e:
        print(f"Error retrieving users: {e}")
        return []

# Analytics functions
def log_extraction_event(
        user_id, 
        file_name, 
        file_type, 
        file_size_bytes, 
        processing_time, 
        success, 
        ocr_used=False
    ):
    """
    Log a text extraction event
    
    Args:
        user_id: Identifier for the user
        file_name: Name of the processed file
        file_type: Type of file processed
        file_size_bytes: Size of file in bytes
        processing_time: Time taken to process in seconds
        success: Whether extraction was successful
        ocr_used: Whether OCR was used
    """
    try:
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO extraction_logs 
            (user_id, file_name, file_type, file_size_bytes, processing_time, success, ocr_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, file_name, file_type, file_size_bytes, processing_time, 
             1 if success else 0, 1 if ocr_used else 0)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging extraction event: {e}")

def get_analytics_summary(username=None):
    """
    Get a summary of usage statistics for display
    
    Args:
        username: Optional username to filter statistics for a specific user
        
    Returns:
        Dictionary with summary statistics
    """
    try:
        conn = get_db_connection()
        
        # Get total files processed
        if username:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM extraction_logs WHERE user_id = ?",
                (username,)
            )
        else:
            cursor = conn.execute("SELECT COUNT(*) FROM extraction_logs")
        total_files = cursor.fetchone()[0]
        
        # Get successful extractions
        if username:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM extraction_logs WHERE success = 1 AND user_id = ?",
                (username,)
            )
        else:
            cursor = conn.execute("SELECT COUNT(*) FROM extraction_logs WHERE success = 1")
        successful = cursor.fetchone()[0]
        
        # Get OCR usage
        if username:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM extraction_logs WHERE ocr_used = 1 AND user_id = ?",
                (username,)
            )
        else:
            cursor = conn.execute("SELECT COUNT(*) FROM extraction_logs WHERE ocr_used = 1")
        ocr_usage = cursor.fetchone()[0]
        
        # Get average processing time
        if username:
            cursor = conn.execute(
                "SELECT AVG(processing_time) FROM extraction_logs WHERE user_id = ?",
                (username,)
            )
        else:
            cursor = conn.execute("SELECT AVG(processing_time) FROM extraction_logs")
        avg_time = cursor.fetchone()[0] or 0
        
        # Get top file types
        if username:
            cursor = conn.execute(
                "SELECT file_type, COUNT(*) as count FROM extraction_logs WHERE user_id = ? GROUP BY file_type ORDER BY count DESC LIMIT 5",
                (username,)
            )
        else:
            cursor = conn.execute(
                "SELECT file_type, COUNT(*) as count FROM extraction_logs GROUP BY file_type ORDER BY count DESC LIMIT 5"
            )
        top_file_types = cursor.fetchall()
        
        # Get file size distribution
        if username:
            cursor = conn.execute(
                """
                SELECT 
                    SUM(CASE WHEN file_size_bytes < 1048576 THEN 1 ELSE 0 END) as small,
                    SUM(CASE WHEN file_size_bytes >= 1048576 AND file_size_bytes < 5242880 THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN file_size_bytes >= 5242880 AND file_size_bytes < 10485760 THEN 1 ELSE 0 END) as large,
                    SUM(CASE WHEN file_size_bytes >= 10485760 THEN 1 ELSE 0 END) as very_large
                FROM extraction_logs
                WHERE user_id = ?
                """,
                (username,)
            )
        else:
            cursor = conn.execute(
                """
                SELECT 
                    SUM(CASE WHEN file_size_bytes < 1048576 THEN 1 ELSE 0 END) as small,
                    SUM(CASE WHEN file_size_bytes >= 1048576 AND file_size_bytes < 5242880 THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN file_size_bytes >= 5242880 AND file_size_bytes < 10485760 THEN 1 ELSE 0 END) as large,
                    SUM(CASE WHEN file_size_bytes >= 10485760 THEN 1 ELSE 0 END) as very_large
                FROM extraction_logs
                """
            )
        size_row = cursor.fetchone()
        file_sizes = {
            "0-1MB": size_row[0] or 0,
            "1-5MB": size_row[1] or 0,
            "5-10MB": size_row[2] or 0,
            "10MB+": size_row[3] or 0
        }
        
        # Get usage trend (last 7 days)
        if username:
            cursor = conn.execute(
                """
                SELECT 
                    date(timestamp) as day, 
                    COUNT(*) as count 
                FROM extraction_logs 
                WHERE user_id = ?
                GROUP BY day 
                ORDER BY day DESC 
                LIMIT 7
                """,
                (username,)
            )
        else:
            cursor = conn.execute(
                """
                SELECT 
                    date(timestamp) as day, 
                    COUNT(*) as count 
                FROM extraction_logs 
                GROUP BY day 
                ORDER BY day DESC 
                LIMIT 7
                """
            )
        usage_trend = cursor.fetchall()
        usage_trend_days = [row[0] for row in reversed(usage_trend)]
        usage_trend_counts = [row[1] for row in reversed(usage_trend)]
        
        # Get top users (admin only, not filtered by username)
        if not username:
            cursor = conn.execute(
                """
                SELECT 
                    user_id, 
                    COUNT(*) as count 
                FROM extraction_logs 
                GROUP BY user_id 
                ORDER BY count DESC 
                LIMIT 5
                """
            )
            top_users = cursor.fetchall()
        else:
            top_users = []
        
        conn.close()
        
        # Calculate success rate and OCR usage rate
        successful_rate = (successful / total_files * 100) if total_files > 0 else 0
        ocr_usage_rate = (ocr_usage / total_files * 100) if total_files > 0 else 0
        
        # Return the analytics summary
        return {
            "total_processed": total_files,
            "success_rate": round(successful_rate, 1),
            "ocr_usage": round(ocr_usage_rate, 1),
            "avg_processing_time": round(avg_time, 2),
            "top_file_types": top_file_types,
            "file_sizes": file_sizes,
            "usage_trend": {
                "days": usage_trend_days,
                "counts": usage_trend_counts
            },
            "top_users": top_users
        }
    except Exception as e:
        print(f"Error getting analytics summary: {e}")
        return {
            "total_processed": 0,
            "success_rate": 0,
            "ocr_usage": 0,
            "avg_processing_time": 0,
            "top_file_types": [],
            "file_sizes": {"0-1MB": 0, "1-5MB": 0, "5-10MB": 0, "10MB+": 0},
            "usage_trend": {
                "days": [],
                "counts": []
            },
            "top_users": []
        }

def reset_analytics():
    """
    Reset all analytics data
    """
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM extraction_logs")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error resetting analytics: {e}")

def export_analytics_to_csv():
    """
    Export analytics data to CSV format
    
    Returns:
        CSV data as string
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM extraction_logs ORDER BY timestamp DESC")
        
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(columns)
        
        # Write data
        for row in rows:
            writer.writerow(row)
        
        conn.close()
        return output.getvalue()
    except Exception as e:
        print(f"Error exporting analytics to CSV: {e}")
        return ""

def save_user_feedback(username, feedback_type, feedback_text, rating):
    """
    Save user feedback to the database
    
    Args:
        username: Username of the user providing feedback
        feedback_type: Type of feedback (e.g., 'bug', 'feature', 'general')
        feedback_text: The actual feedback text
        rating: Numeric rating (e.g., 1-5)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO user_feedback (username, feedback_type, feedback_text, rating)
            VALUES (?, ?, ?, ?)
            """,
            (username, feedback_type, feedback_text, rating)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving user feedback: {e}")
        return False

def get_user_feedback(username=None):
    """
    Get user feedback from the database
    
    Args:
        username: Optional username to filter by. If None, returns all feedback.
        
    Returns:
        List of feedback dictionaries
    """
    try:
        conn = get_db_connection()
        
        if username:
            cursor = conn.execute(
                "SELECT * FROM user_feedback WHERE username = ? ORDER BY timestamp DESC",
                (username,)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM user_feedback ORDER BY timestamp DESC"
            )
        
        feedback = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return feedback
    except Exception as e:
        print(f"Error retrieving feedback: {e}")
        return []

# Data retention features
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
            import json
            return json.dumps(result, indent=2, default=str)
        elif format_type == "csv":
            import csv
            import io
            
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

# Initialize the database
init_database()

# Migrate existing data if available
migrate_json_to_db()