#!/usr/bin/env python3
"""
Health check script for Universal Text Extractor
Can be used for monitoring and load balancer health checks
"""

import sys
import sqlite3
import os
from pathlib import Path

# Make requests optional for basic health checks
try:
    import requests
    has_requests = True
except ImportError:
    has_requests = False

def check_web_service(host="localhost", port=5000):
    """Check if the web service is responding"""
    try:
        response = requests.get(f"http://{host}:{port}/_stcore/health", timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Web service check failed: {e}")
        return False

def check_database():
    """Check if the database is accessible"""
    try:
        db_path = Path("data/text_extractor.db")
        if not db_path.exists():
            print("Database file does not exist")
            return False
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        cursor.fetchone()
        conn.close()
        return True
    except Exception as e:
        print(f"Database check failed: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import streamlit
        import PIL
        import pytesseract
        return True
    except ImportError as e:
        print(f"Dependency check failed: {e}")
        return False

def check_data_directory():
    """Check if data directory exists and is writable"""
    try:
        data_dir = Path("data")
        if not data_dir.exists():
            data_dir.mkdir(parents=True)
        
        # Test write access
        test_file = data_dir / "health_check.tmp"
        test_file.write_text("test")
        test_file.unlink()
        return True
    except Exception as e:
        print(f"Data directory check failed: {e}")
        return False

def main():
    """Run all health checks"""
    checks = [
        ("Dependencies", check_dependencies),
        ("Data Directory", check_data_directory),
        ("Database", check_database),
        ("Web Service", check_web_service),
    ]
    
    all_passed = True
    
    print("🏥 Universal Text Extractor Health Check")
    print("=" * 40)
    
    for name, check_func in checks:
        try:
            result = check_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{name:15} {status}")
            if not result:
                all_passed = False
        except Exception as e:
            print(f"{name:15} ❌ ERROR: {e}")
            all_passed = False
    
    print("=" * 40)
    if all_passed:
        print("🎉 All health checks passed!")
        sys.exit(0)
    else:
        print("⚠️  Some health checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()