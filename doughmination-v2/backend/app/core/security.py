"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Security utilities for authentication and authorization
Handles JWT tokens, password hashing, and Turnstile verification
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import bcrypt
from fastapi import HTTPException, status

from app.core.config import (
    JWT_SECRET, 
    JWT_ALGORITHM, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    TURNSTILE_SECRET
)

logger = logging.getLogger(__name__)

# ============================================================================
# PASSWORD HASHING
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    bcrypt only considers the first 72 bytes of input, and bcrypt>=4.1
    raises if a longer value is passed. We truncate to 72 bytes to keep
    behaviour stable and avoid errors on long passwords.
    """
    password_bytes = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Returns False (rather than raising) if the stored hash is missing or
    malformed, e.g. a record left behind by a failed startup.
    """
    if not hashed_password:
        return False
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False

# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

# ============================================================================
# TURNSTILE VERIFICATION
# ============================================================================

async def verify_turnstile_token(token: str, remote_ip: Optional[str] = None) -> bool:
    """
    Verify Cloudflare Turnstile token
    
    Args:
        token: Turnstile response token
        remote_ip: Client IP address (optional)
    
    Returns:
        True if verification succeeds
    
    Raises:
        HTTPException: If verification fails or server error
    """
    if not TURNSTILE_SECRET:
        logger.error("DOUGH_TURNSILE_SECRET environment variable not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )
    
    verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    
    data = {
        "secret": TURNSTILE_SECRET,
        "response": token,
    }
    
    if remote_ip:
        data["remoteip"] = remote_ip
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(verify_url, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get("success", False):
                logger.warning(f"Turnstile verification failed: {result.get('error-codes', [])}")
                return False
            
            logger.info("Turnstile verification successful")
            return True
            
    except httpx.RequestError as e:
        logger.error(f"Failed to verify Turnstile token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify security token"
        )
    except Exception as e:
        logger.error(f"Unexpected error during Turnstile verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security verification error"
        )