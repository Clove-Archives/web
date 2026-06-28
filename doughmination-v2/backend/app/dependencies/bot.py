"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Bot authentication dependencies
For Discord bot API access
"""

from typing import Optional
from fastapi import Header, HTTPException, status

from app.services.bot_token_service import verify_bot_token

async def verify_bot_access(
    authorization: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None)
) -> bool:
    """
    Verify bot access via Authorization header and User-Agent
    
    Expected format:
    - Authorization: Bearer <token>
    - User-Agent: CloveShortcuts/<version>
    
    Args:
        authorization: Authorization header
        user_agent: User-Agent header
    
    Returns:
        True if authenticated
    
    Raises:
        HTTPException: If authentication fails
    """
    # Validate User-Agent
    if not user_agent or not user_agent.startswith("CloveShortcuts/"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid User-Agent. Expected 'CloveShortcuts/<version>'"
        )
    
    # Validate Authorization header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = parts[1]
    
    # Verify token
    if not verify_bot_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bot access token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return True