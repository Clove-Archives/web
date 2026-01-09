from fastapi import APIRouter, Depends, HTTPException, Header, status
from typing import Optional, List
from pydantic import BaseModel

from bot_tokens import verify_bot_token, regenerate_bot_token
from auth import get_current_user
from users import get_user_by_username
from models import User

router = APIRouter(prefix="/api/bot", tags=["bot"])


# ============================================================================
# AUTHENTICATION DEPENDENCY
# ============================================================================

async def verify_bot_access(
    authorization: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None)
) -> bool:
    """
    Verify bot access via Authorization header
    Expected format: Bearer <token>
    Also validates User-Agent starts with "CloveShortcuts/"
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


# ============================================================================
# MODELS
# ============================================================================

class TokenRegenerateResponse(BaseModel):
    success: bool
    message: str
    new_token: str


class HealthResponse(BaseModel):
    status: str
    message: str
    authenticated: bool


class FronterUpdateRequest(BaseModel):
    member_id: str


class MultiSwitchRequest(BaseModel):
    member_ids: List[str]


class FronterUpdateResponse(BaseModel):
    success: bool
    message: str
    fronters: list


class MultiSwitchResponse(BaseModel):
    status: str
    message: str
    fronters: list
    count: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def bot_health_check(authenticated: bool = Depends(verify_bot_access)):
    """
    Health check endpoint for the bot to verify connectivity and authentication
    """
    return HealthResponse(
        status="ok",
        message="Bot API is operational",
        authenticated=authenticated
    )


@router.post("/token/regenerate", response_model=TokenRegenerateResponse)
async def regenerate_token(
    current_user: User = Depends(get_current_user)
):
    """
    Regenerate (terminate and create new) bot access token
    Only accessible by users with is_owner=True or via the bot's current token
    """
    # Check if user is owner
    if not current_user.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can regenerate the bot access token"
        )
    
    # Regenerate the token
    new_token = regenerate_bot_token()
    
    return TokenRegenerateResponse(
        success=True,
        message="Bot access token has been regenerated. Update your bot's .env file with the new token.",
        new_token=new_token
    )


# Alternative endpoint that can be called with bot token
@router.post("/token/regenerate-self")
async def regenerate_token_self(authenticated: bool = Depends(verify_bot_access)):
    """
    Regenerate bot access token using the current bot token
    This allows the bot to regenerate its own token if needed
    """
    new_token = regenerate_bot_token()
    
    return TokenRegenerateResponse(
        success=True,
        message="Bot access token has been regenerated. The old token is now invalid.",
        new_token=new_token
    )


# ============================================================================
# FRONTING ENDPOINTS
# ============================================================================

@router.get("/system/info")
async def get_system_info_for_bot(authenticated: bool = Depends(verify_bot_access)):
    """
    Get system information (example protected endpoint)
    """
    from pluralkit import get_system
    
    try:
        system_data = await get_system()
        return {
            "success": True,
            "data": system_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch system info: {str(e)}"
        )


@router.get("/members")
async def get_members_for_bot(authenticated: bool = Depends(verify_bot_access)):
    """
    Get all members (example protected endpoint)
    """
    from pluralkit import get_members
    from tags import enrich_members_with_tags
    from member_status import enrich_members_with_status
    
    try:
        members_data = await get_members()
        members_with_tags = enrich_members_with_tags(members_data)
        members_with_status = enrich_members_with_status(members_with_tags)
        
        return {
            "success": True,
            "data": members_with_status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch members: {str(e)}"
        )


@router.get("/fronters")
async def get_fronters_for_bot(authenticated: bool = Depends(verify_bot_access)):
    """
    Get current fronters (example protected endpoint)
    """
    from pluralkit import get_fronters
    
    try:
        fronters_data = await get_fronters()
        
        return {
            "success": True,
            "data": fronters_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fronters: {str(e)}"
        )


@router.post("/switch", response_model=MultiSwitchResponse)
async def bot_multi_switch(
    request: MultiSwitchRequest,
    authenticated: bool = Depends(verify_bot_access)
):
    """
    Switch to multiple fronters at once (bot endpoint)
    This is the recommended way for the bot to update fronters
    """
    from pluralkit import set_front, get_fronters, get_members
    
    try:
        # Validate that all member IDs exist
        all_members = await get_members()
        valid_member_ids = {member['id'] for member in all_members}
        
        invalid_ids = [mid for mid in request.member_ids if mid not in valid_member_ids]
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid member IDs: {', '.join(invalid_ids)}"
            )
        
        # Set the front
        await set_front(request.member_ids)
        
        # Get updated fronters to return
        updated_fronters = await get_fronters()
        
        return MultiSwitchResponse(
            status="success",
            message="Fronters updated successfully",
            fronters=updated_fronters.get('members', []),
            count=len(request.member_ids)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch fronters: {str(e)}"
        )


@router.post("/fronters/add", response_model=FronterUpdateResponse)
async def add_fronter(
    request: FronterUpdateRequest,
    authenticated: bool = Depends(verify_bot_access)
):
    """
    Add a member to the front
    DEPRECATED: Use /api/bot/switch instead for better control
    """
    from pluralkit import get_fronters, set_front
    
    try:
        # Get current fronters
        current_fronters = await get_fronters()
        current_member_ids = [member['id'] for member in current_fronters.get('members', [])]
        
        # Check if member is already fronting
        if request.member_id in current_member_ids:
            return FronterUpdateResponse(
                success=False,
                message=f"Member {request.member_id} is already fronting",
                fronters=current_fronters.get('members', [])
            )
        
        # Add the new member
        new_member_ids = current_member_ids + [request.member_id]
        
        # Update fronters
        await set_front(new_member_ids)
        updated_fronters = await get_fronters()
        
        return FronterUpdateResponse(
            success=True,
            message=f"Successfully added member to front",
            fronters=updated_fronters.get('members', [])
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add fronter: {str(e)}"
        )


@router.post("/fronters/remove", response_model=FronterUpdateResponse)
async def remove_fronter(
    request: FronterUpdateRequest,
    authenticated: bool = Depends(verify_bot_access)
):
    """
    Remove a member from the front
    DEPRECATED: Use /api/bot/switch instead for better control
    """
    from pluralkit import get_fronters, set_front
    
    try:
        # Get current fronters
        current_fronters = await get_fronters()
        current_member_ids = [member['id'] for member in current_fronters.get('members', [])]
        
        # Check if member is currently fronting
        if request.member_id not in current_member_ids:
            return FronterUpdateResponse(
                success=False,
                message=f"Member {request.member_id} is not currently fronting",
                fronters=current_fronters.get('members', [])
            )
        
        # Remove the member
        new_member_ids = [mid for mid in current_member_ids if mid != request.member_id]
        
        # Update fronters
        await set_front(new_member_ids)
        updated_fronters = await get_fronters()
        
        return FronterUpdateResponse(
            success=True,
            message=f"Successfully removed member from front",
            fronters=updated_fronters.get('members', [])
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove fronter: {str(e)}"
        )