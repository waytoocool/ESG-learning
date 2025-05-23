# services/token.py
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

def generate_registration_token(user_id):
    """
    Generate a secure token for user registration
    
    Args:
        user_id: The ID of the user to generate token for
    
    Returns:
        str: Generated token
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(user_id, salt='registration-salt')

def verify_registration_token(token, expiration=86400):  # 24 hours default
    """
    Verify a registration token
    
    Args:
        token (str): Token to verify
        expiration (int): Token expiration time in seconds
    
    Returns:
        int or None: User ID if valid, None if invalid
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_id = serializer.loads(token, salt='registration-salt', max_age=expiration)
        return user_id
    except (SignatureExpired, BadSignature):
        return None

def generate_password_reset_token(user_email):
    """
    Generate a secure token for password reset
    
    Args:
        user_email: The email ID of the user to generate token for
    
    Returns:
        str: Generated token
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(user_id, salt='password-reset-salt')

def verify_password_reset_token(token, expiration=3600):  # 1 hour default
    """
    Verify a password reset token
    
    Args:
        token (str): Token to verify
        expiration (int): Token expiration time in seconds
    
    Returns:
        int or None: User ID if valid, None if invalid
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return user_email
    except (SignatureExpired, BadSignature):
        return None
