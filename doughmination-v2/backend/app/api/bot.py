"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Discord Bot API endpoints
Secure API for bot integration
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from app.models import (
    TokenRegenerateResponse, HealthResponse,
    FronterUpdateRequest, MultiSwitchRequest,
    FronterUpdateResponse, MultiSwitchResponse
)
from app.services.bot_token_service import regenerate_bot_token
from app.services.pluralkit import get_system, get_members, get_fronters, set_front
from app.services.tag_service import enrich_members_with_tags
from app.services.status_service import enrich_members_with_status
from app.dependencies.auth import get_owner_user
from app.dependencies.bot import verify_bot_access
from app.models import User

router = APIRouter(prefix="/api/bot")

# ============================================================================
# HEALTH & TOKEN MANAGEMENT
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def bot_health_check(authenticated: bool = Depends(verify_bot_access)):
    """Health check endpoint for the bot"""
    return HealthResponse(
        status="ok",
        message="Bot API is operational",
        authenticated=authenticated
    )

@router.post("/token/regenerate", response_model=TokenRegenerateResponse)
async def regenerate_token(current_user: User = Depends(get_owner_user)):
    """Regenerate bot access token (owner only)"""
    new_token = regenerate_bot_token()
    
    return TokenRegenerateResponse(
        success=True,
        message="Bot access token has been regenerated. Update your bot's .env file.",
        new_token=new_token
    )

@router.post("/token/regenerate-self", response_model=TokenRegenerateResponse)
async def regenerate_token_self(authenticated: bool = Depends(verify_bot_access)):
    """Regenerate bot access token using current bot token"""
    new_token = regenerate_bot_token()
    
    return TokenRegenerateResponse(
        success=True,
        message="Bot access token has been regenerated. The old token is now invalid.",
        new_token=new_token
    )

# ============================================================================
# SYSTEM INFO ENDPOINTS
# ============================================================================

@router.get("/system/info")
async def get_system_info_for_bot(authenticated: bool = Depends(verify_bot_access)):
    """Get system information"""
    try:
        system_data = await get_system()
        return {"success": True, "data": system_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch system info: {str(e)}"
        )

@router.get("/members")
async def get_members_for_bot(authenticated: bool = Depends(verify_bot_access)):
    """Get all members with tags and status"""
    try:
        members_data = await get_members()
        members_with_tags = enrich_members_with_tags(members_data)
        members_with_status = enrich_members_with_status(members_with_tags)
        
        return {"success": True, "data": members_with_status}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch members: {str(e)}"
        )

@router.get("/fronters")
async def get_fronters_for_bot(authenticated: bool = Depends(verify_bot_access)):
    """Get current fronters"""
    try:
        fronters_data = await get_fronters()
        return {"success": True, "data": fronters_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fronters: {str(e)}"
        )

# ============================================================================
# FRONTING CONTROL ENDPOINTS
# ============================================================================

@router.post("/switch", response_model=MultiSwitchResponse)
async def bot_multi_switch(
    request: MultiSwitchRequest,
    authenticated: bool = Depends(verify_bot_access)
):
    """Switch the system fronts"""
    try:
        # Validate member IDs
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
        
        # Get updated fronters
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
    
# @router