"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Authentication dependencies
Reusable FastAPI dependencies for authentication and authorization
"""

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError

from app.core.security import decode_access_token
from app.services.user_service import get_user_by_username
from app.models import User

# OAuth2 scheme for extracting Bearer token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current authenticated user from JWT token
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        Authenticated user
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Decode and validate token
        payload = decode_access_token(token)
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user from database
        user = get_user_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_optional_user(token: str = Security(oauth2_scheme, scopes=[])) -> User | None:
    """
    Get the current user if authenticated, otherwise None
    Useful for endpoints that work with or without authentication
    
    Args:
        token: JWT token from Authorization header (optional)
    
    Returns:
        Authenticated user or None
    """
    try:
        return await get_current_user(token)
    except (HTTPException, JWTError):
        return None

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Require an admin user for the endpoint
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Admin user
    
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def get_owner_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Require the owner user for the endpoint
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Owner user
    
    Raises:
        HTTPException: If user is not the owner
    """
    if not current_user.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner privileges required"
        )
    return current_user

async def get_pet_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Require a pet user for the endpoint
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Pet user
    
    Raises:
        HTTPException: If user is not a pet
    """
    if not current_user.is_pet:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pet privileges required"
        )
    return current_user