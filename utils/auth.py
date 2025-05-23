import os
import json
import hashlib
import hmac
import base64
import time

# File to store user credentials
USERS_FILE = "users.json"

# Default admin credentials (for initial setup only)
DEFAULT_ADMIN_USERNAME = "admin"
# Generate a secure random password for initial setup
import secrets
import string
def generate_secure_password(length=16):
    """Generate a cryptographically secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# User roles
ROLE_USER = "user"
ROLE_ADMIN = "admin"

def initialize_users():
    """
    Initialize users file if it doesn't exist with default admin account
    """
    if not os.path.exists(USERS_FILE):
        # Generate a secure random password for the default admin
        initial_password = generate_secure_password()
        
        # Display the generated password (in a real system, this would be securely
        # communicated to the administrator via a secure channel)
        print(f"IMPORTANT: Initial admin password generated: {initial_password}")
        print("Please save this password and change it immediately after first login.")
        
        # Create with default admin account
        default_admin = {
            "username": DEFAULT_ADMIN_USERNAME,
            "password_hash": hash_password(initial_password),
            "role": ROLE_ADMIN,
            "created_at": time.time(),
            "require_password_change": True  # Force password change on first login
        }
        
        users_data = {
            "users": [default_admin]
        }
        
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=2)

def get_users():
    """
    Get all users
    """
    if not os.path.exists(USERS_FILE):
        initialize_users()
    
    with open(USERS_FILE, 'r') as f:
        return json.load(f)["users"]

def save_users(users):
    """
    Save users to file
    """
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": users}, f, indent=2)

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
    users = get_users()
    
    for user in users:
        if user["username"] == username:
            if verify_password(user["password_hash"], password):
                return user
    
    return None

def get_user_by_username(username):
    """
    Get a user by username
    
    Args:
        username: Username
    
    Returns:
        User dict if found, None otherwise
    """
    users = get_users()
    
    for user in users:
        if user["username"] == username:
            return user
    
    return None

def add_user(username, password, role=ROLE_USER):
    """
    Add a new user
    
    Args:
        username: Username
        password: Password
        role: User role (default: ROLE_USER)
    
    Returns:
        True if added, False if username already exists
    """
    if get_user_by_username(username):
        return False
    
    users = get_users()
    
    new_user = {
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
        "created_at": time.time(),
        "require_password_change": False
    }
    
    users.append(new_user)
    save_users(users)
    
    return True

def change_password(username, new_password):
    """
    Change a user's password
    
    Args:
        username: Username
        new_password: New password
    
    Returns:
        True if changed, False if user not found
    """
    users = get_users()
    
    for i, user in enumerate(users):
        if user["username"] == username:
            users[i]["password_hash"] = hash_password(new_password)
            users[i]["require_password_change"] = False
            save_users(users)
            return True
    
    return False

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