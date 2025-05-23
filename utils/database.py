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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        require_password_change BOOLEAN DEFAULT 0
    )
    ''')
    
    # Create extraction_logs table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS extraction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size_bytes INTEGER NOT NULL,
        processing_time REAL NOT NULL,
        ocr_used BOOLEAN NOT NULL,
        success BOOLEAN NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create user_feedback table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS user_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        feedback_type TEXT NOT NULL,
        feedback_text TEXT NOT NULL,
        rating INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    ''')
    
    # Create file_type_stats table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS file_type_stats (
        file_type TEXT PRIMARY KEY,
        count INTEGER NOT NULL DEFAULT 0
    )
    ''')
    
    # Create file_size_stats table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS file_size_stats (
        size_range TEXT PRIMARY KEY,
        count INTEGER NOT NULL DEFAULT 0
    )
    ''')
    
    # Create daily_stats table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS daily_stats (
        date TEXT PRIMARY KEY,
        total INTEGER NOT NULL DEFAULT 0,
        successful INTEGER NOT NULL DEFAULT 0,
        failed INTEGER NOT NULL DEFAULT 0,
        ocr_used INTEGER NOT NULL DEFAULT 0
    )
    ''')
    
    # Create daily_file_types table for daily file type breakdown
    conn.execute('''
    CREATE TABLE IF NOT EXISTS daily_file_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        file_type TEXT NOT NULL,
        count INTEGER NOT NULL DEFAULT 0,
        UNIQUE(date, file_type)
    )
    ''')
    
    conn.commit()
    conn.close()

def migrate_json_to_db():
    """
    Migrate existing JSON data to the database if available
    """
    # Migrate users
    if os.path.exists("users.json") or os.path.exists(os.path.join(DB_DIR, "users.json")):
        try:
            users_file = "users.json" if os.path.exists("users.json") else os.path.join(DB_DIR, "users.json")
            with open(users_file, 'r') as f:
                users_data = json.load(f)
                
                conn = get_db_connection()
                for user in users_data.get("users", []):
                    # Check if user already exists
                    cursor = conn.execute("SELECT id FROM users WHERE username = ?", (user["username"],))
                    if cursor.fetchone() is None:
                        conn.execute(
                            "INSERT INTO users (username, password_hash, role, require_password_change) VALUES (?, ?, ?, ?)",
                            (user["username"], user["password_hash"], user["role"], user.get("require_password_change", 0))
                        )
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Error migrating users: {e}")
    
    # Migrate analytics
    if os.path.exists("usage_statistics.json") or os.path.exists(os.path.join(DB_DIR, "usage_statistics.json")):
        try:
            stats_file = "usage_statistics.json" if os.path.exists("usage_statistics.json") else os.path.join(DB_DIR, "usage_statistics.json")
            with open(stats_file, 'r') as f:
                stats_data = json.load(f)
                
                conn = get_db_connection()
                
                # Migrate file types stats
                for file_type, count in stats_data.get("file_types", {}).items():
                    conn.execute(
                        "INSERT OR REPLACE INTO file_type_stats (file_type, count) VALUES (?, ?)",
                        (file_type, count)
                    )
                
                # Migrate file size stats
                for size_range, count in stats_data.get("file_sizes", {}).items():
                    conn.execute(
                        "INSERT OR REPLACE INTO file_size_stats (size_range, count) VALUES (?, ?)",
                        (size_range, count)
                    )
                
                # Migrate daily stats
                for date, count in stats_data.get("processing_dates", {}).items():
                    # Look up the daily usage details
                    daily_data = stats_data.get("daily_usage", {}).get(date, {})
                    successful = daily_data.get("successful", 0)
                    failed = daily_data.get("failed", 0)
                    ocr_used = daily_data.get("ocr_used", 0)
                    
                    conn.execute(
                        "INSERT OR REPLACE INTO daily_stats (date, total, successful, failed, ocr_used) VALUES (?, ?, ?, ?, ?)",
                        (date, count, successful, failed, ocr_used)
                    )
                    
                    # Migrate daily file type breakdown
                    for file_type, type_count in daily_data.get("types", {}).items():
                        conn.execute(
                            "INSERT OR REPLACE INTO daily_file_types (date, file_type, count) VALUES (?, ?, ?)",
                            (date, file_type, type_count)
                        )
                
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Error migrating analytics: {e}")

# User management functions
def get_user_by_username(username):
    """
    Get a user by username
    
    Args:
        username: Username
    
    Returns:
        User dict if found, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
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
    if get_user_by_username(username):
        return False
    
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, require_password_change) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, require_password_change)
        )
        conn.commit()
        result = True
    except:
        result = False
    
    conn.close()
    return result

def change_password(username, new_password_hash):
    """
    Change a user's password
    
    Args:
        username: Username
        new_password_hash: New hashed password
    
    Returns:
        True if changed, False if user not found
    """
    conn = get_db_connection()
    cursor = conn.execute(
        "UPDATE users SET password_hash = ?, require_password_change = 0 WHERE username = ?",
        (new_password_hash, username)
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success

def get_all_users():
    """
    Get all users
    
    Returns:
        List of user dicts
    """
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM users ORDER BY username")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return users

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
        
        # Log the extraction event
        conn.execute(
            "INSERT INTO extraction_logs (user_id, file_name, file_type, file_size_bytes, processing_time, ocr_used, success) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, file_name, file_type, file_size_bytes, processing_time, ocr_used, success)
        )
        
        # Update file type statistics
        conn.execute(
            "INSERT INTO file_type_stats (file_type, count) VALUES (?, 1) ON CONFLICT(file_type) DO UPDATE SET count = count + 1",
            (file_type,)
        )
        
        # Update file size statistics
        size_mb = file_size_bytes / (1024 * 1024)
        if size_mb <= 1:
            size_range = "0-1MB"
        elif size_mb <= 5:
            size_range = "1-5MB"
        elif size_mb <= 10:
            size_range = "5-10MB"
        else:
            size_range = "10MB+"
            
        conn.execute(
            "INSERT INTO file_size_stats (size_range, count) VALUES (?, 1) ON CONFLICT(size_range) DO UPDATE SET count = count + 1",
            (size_range,)
        )
        
        # Update daily statistics
        today = datetime.date.today().isoformat()
        
        conn.execute(
            "INSERT INTO daily_stats (date, total, successful, failed, ocr_used) VALUES (?, 1, ?, ?, ?) ON CONFLICT(date) DO UPDATE SET total = total + 1, successful = successful + ?, failed = failed + ?, ocr_used = ocr_used + ?",
            (today, 1 if success else 0, 0 if success else 1, 1 if ocr_used else 0, 1 if success else 0, 0 if success else 1, 1 if ocr_used else 0)
        )
        
        # Update daily file type breakdown
        conn.execute(
            "INSERT INTO daily_file_types (date, file_type, count) VALUES (?, ?, 1) ON CONFLICT(date, file_type) DO UPDATE SET count = count + 1",
            (today, file_type)
        )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error logging extraction event: {e}")

def get_analytics_summary():
    """
    Get a summary of usage statistics for display
    
    Returns:
        Dictionary with summary statistics
    """
    try:
        conn = get_db_connection()
        
        # Get total files processed
        cursor = conn.execute("SELECT COUNT(*) as count FROM extraction_logs")
        total_files = cursor.fetchone()['count']
        
        # Get successful extractions
        cursor = conn.execute("SELECT COUNT(*) as count FROM extraction_logs WHERE success = 1")
        successful = cursor.fetchone()['count']
        
        # Get OCR usage
        cursor = conn.execute("SELECT COUNT(*) as count FROM extraction_logs WHERE ocr_used = 1")
        ocr_usage = cursor.fetchone()['count']
        
        # Get average processing time
        cursor = conn.execute("SELECT AVG(processing_time) as avg_time FROM extraction_logs")
        avg_time = cursor.fetchone()['avg_time'] or 0
        
        # Get top file types
        cursor = conn.execute("SELECT file_type, count FROM file_type_stats ORDER BY count DESC LIMIT 5")
        top_file_types = [(row['file_type'], row['count']) for row in cursor.fetchall()]
        
        # Get file size distribution
        cursor = conn.execute("SELECT size_range, count FROM file_size_stats")
        file_sizes = {row['size_range']: row['count'] for row in cursor.fetchall()}
        
        # Get top users
        cursor = conn.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM extraction_logs 
            GROUP BY user_id 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_users = [(row['user_id'], row['count']) for row in cursor.fetchall()]
        
        # Get usage over time (last 7 days)
        today = datetime.date.today()
        last_week = [(today - datetime.timedelta(days=i)).isoformat() for i in range(7)]
        last_week.reverse()  # Oldest first
        
        usage_trend = []
        for day in last_week:
            cursor = conn.execute("SELECT total FROM daily_stats WHERE date = ?", (day,))
            row = cursor.fetchone()
            usage_trend.append(row['total'] if row else 0)
        
        conn.close()
        
        # Calculate percentages
        successful_rate = (successful / total_files * 100) if total_files > 0 else 0
        ocr_usage_rate = (ocr_usage / total_files * 100) if total_files > 0 else 0
        
        # Prepare summary
        summary = {
            "total_files_processed": total_files,
            "successful_extractions": successful,
            "successful_rate": successful_rate,
            "ocr_usage": ocr_usage,
            "ocr_usage_rate": ocr_usage_rate,
            "avg_processing_time": avg_time,
            "top_file_types": top_file_types,
            "file_sizes": file_sizes,
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
            "total_files_processed": 0,
            "successful_extractions": 0,
            "successful_rate": 0,
            "ocr_usage": 0,
            "ocr_usage_rate": 0,
            "avg_processing_time": 0,
            "top_file_types": [],
            "file_sizes": {"0-1MB": 0, "1-5MB": 0, "5-10MB": 0, "10MB+": 0},
            "top_users": [],
            "usage_trend": {
                "days": [],
                "counts": []
            }
        }

def reset_analytics():
    """
    Reset all analytics data
    """
    try:
        conn = get_db_connection()
        
        # Truncate all analytics tables but keep the users table
        conn.execute("DELETE FROM extraction_logs")
        conn.execute("DELETE FROM file_type_stats")
        conn.execute("DELETE FROM file_size_stats")
        conn.execute("DELETE FROM daily_stats")
        conn.execute("DELETE FROM daily_file_types")
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error resetting analytics: {e}")
        return False

def export_analytics_to_csv():
    """
    Export analytics data to CSV format
    
    Returns:
        CSV data as string
    """
    try:
        conn = get_db_connection()
        
        # Create CSV content
        csv_lines = ["date,total,successful,failed,ocr_used,file_types"]
        
        # Get daily stats with file type breakdown
        cursor = conn.execute("""
            SELECT d.date, d.total, d.successful, d.failed, d.ocr_used, 
                   GROUP_CONCAT(df.file_type || ': ' || df.count) as file_types
            FROM daily_stats d
            LEFT JOIN daily_file_types df ON d.date = df.date
            GROUP BY d.date
            ORDER BY d.date
        """)
        
        for row in cursor.fetchall():
            file_types_str = row['file_types'] if row['file_types'] else ""
            csv_lines.append(f"{row['date']},{row['total']},{row['successful']},{row['failed']},{row['ocr_used']},\"{file_types_str}\"")
        
        conn.close()
        
        return "\n".join(csv_lines)
        
    except Exception as e:
        print(f"Error exporting analytics to CSV: {e}")
        return "Error generating CSV export"

# Initialize the database
init_database()

# Migrate existing data if available
migrate_json_to_db()