import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

# --- Password Hashing ---
def hash_password(password: str) -> bytes:
    """Hashes a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password: str, hashed_password: bytes) -> bool:
    """Checks a password against a stored hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# --- JWT Token Management ---
JWT_SECRET = os.getenv("JWT_SECRET", "your-default-super-secret-key") # Use a strong, random secret in production!
JWT_ALGORITHM = "HS256"
JWT_EXP_DAYS = 1

def create_token(account_id: int, email: str, role: str) -> str:
    """Creates a JWT for a given user."""
    payload = {
        "iat": datetime.now(timezone.utc), # Issued at
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXP_DAYS), # Expiration
        "sub": account_id, # Subject (the user's unique ID)
        "email": email,
        "role": role,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict | None:
    """Verifies a JWT and returns its payload if valid."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None