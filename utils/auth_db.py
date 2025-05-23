import os
import hashlib
import hmac
import base64
import time
from utils.database import get_user_by_username, add_user as db_add_user, change_password as db_change_password

# User roles
ROLE_USER = "user"
ROLE_ADMIN = "admin"

# Default admin credentials (for initial setup only)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"  # Would be changed on first use

def initialize_users():
    """
    Initialize database with default admin account if no admin exists
    """
    # Check if admin user exists
    admin = get_user_by_username(DEFAULT_ADMIN_USERNAME)
    
    if not admin:
        # Create default admin
        password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
        db_add_user(
            DEFAULT_ADMIN_USERNAME, 
            password_hash, 
            ROLE_ADMIN, 
            require_password_change=True
        )

def hash_password(password):
    """
    Hash a password using a secure method
    
    In a production environment, use a proper password hashing library like bcrypt
    """
    # This is a simple hash - for production use a proper password hashing library
    salt = b"static_salt_for_demo"  # In production, use a random salt per user
    return base64.b64encode(
        hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    ).decode()

def verify_password(stored_hash, password):
    """
    Verify a password against its hash
    """
    calc_hash = hash_password(password)
    return hmac.compare_digest(stored_hash, calc_hash)

def authenticate_user(username, password):
    """
    Authenticate a user
    
    Args:
        username: Username
        password: Password
    
    Returns:
        User dict if authenticated, None otherwise
    """
    user = get_user_by_username(username)
    
    if user and verify_password(user["password_hash"], password):
        return user
    
    return None

def add_user(username, password, role=ROLE_USER):
    """
    Add a new user with hashed password
    
    Args:
        username: Username
        password: Clear text password
        role: User role
    
    Returns:
        True if added, False if username already exists
    """
    password_hash = hash_password(password)
    return db_add_user(username, password_hash, role)

def change_password(username, new_password):
    """
    Change a user's password
    
    Args:
        username: Username
        new_password: New password (clear text)
    
    Returns:
        True if changed, False if user not found
    """
    new_password_hash = hash_password(new_password)
    return db_change_password(username, new_password_hash)

def is_admin(username):
    """
    Check if a user is an admin
    
    Args:
        username: Username
    
    Returns:
        True if admin, False otherwise
    """
    user = get_user_by_username(username)
    
    if user and user["role"] == ROLE_ADMIN:
        return True
    
    return False