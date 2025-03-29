from datetime import datetime, timedelta
import secrets
import string
from flask import current_app
import jwt
from jwt.exceptions import PyJWTError
from app import bcrypt
from app.models.user import User

def generate_password_hash(password):
    """Generate a secure hash of the password"""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password_hash(hashed_password, password):
    """Check if the password matches the hash"""
    return bcrypt.check_password_hash(hashed_password, password)

def generate_token(user_id, expires_in=86400):
    """Generate a JWT token for the user"""
    payload = {
        'sub': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=expires_in)
    }
    
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def decode_token(token):
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload['sub']  # User ID
    except PyJWTError:
        return None

def generate_password_reset_token(user_id, expires_in=3600):
    """Generate a password reset token"""
    payload = {
        'sub': user_id,
        'type': 'password_reset',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=expires_in)
    }
    
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_password_reset_token(token):
    """Verify a password reset token"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        
        if payload.get('type') != 'password_reset':
            return None
            
        return payload['sub']  # User ID
    except PyJWTError:
        return None

def generate_random_password(length=12):
    """Generate a strong random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def encrypt_sensitive_data(data, key=None):
    """Encrypt sensitive data (placeholder for proper encryption)"""
    # In a real implementation, use a proper encryption library
    # This is just a placeholder for the concept
    # Example: use Fernet symmetric encryption from cryptography library
    return f"ENCRYPTED:{data}"

def decrypt_sensitive_data(encrypted_data, key=None):
    """Decrypt sensitive data (placeholder for proper decryption)"""
    # In a real implementation, use a proper encryption library
    # This is just a placeholder for the concept
    if encrypted_data.startswith("ENCRYPTED:"):
        return encrypted_data[10:]  # Remove the ENCRYPTED: prefix
    return encrypted_data
