"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Member status API endpoints
Handles custom status messages for members
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Body

from app.services.status_service import (
    get_member_status, set_member_status, clear_member_status
)
from app.dependencies.auth import get_admin_user

router = APIRouter()

@router.get("/members/{member_identifier}/status")
async def get_member_status_endpoint(member_identifier: str):
    """Get status for a specific member (public endpoint)"""
    try:
        status = get_member_status(member_identifier)
        
        return {
            "success": True,
            "member_identifier": member_identifier,
            "status": status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch member status: {str(e)}"
        )

@router.post("/members/{member_identifier}/status")
async def set_member_status_endpoint(
    member_identifier: str,
    status_data: Dict[str, Any] = Body(...),
    user=Depends(get_admin_user)
):
    """Set or update status for a member (admin only)"""
    try:
        status_text = status_data.get("text")
        emoji = status_data.get("emoji")
        
        if not status_text:
            raise HTTPException(
                status_code=400,
                detail="Status text is required"
            )
        
        # Validate status text length
        if len(status_text) > 100:
            raise HTTPException(
                status_code=400,
                detail="Status text must be 100 characters or less"
            )
        
        status = set_member_status(member_identifier, status_text, emoji)
        
        return {
            "success": True,
            "message": f"Status updated for {member_identifier}",
            "status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set member status: {str(e)}"
        )

@router.delete("/members/{member_identifier}/status")
async def clear_member_status_endpoint(
    member_identifier: str,
    user=Depends(get_admin_user)
):
    """Clear status for a member (admin only)"""
    try:
        success = clear_member_status(member_identifier)
        
        if success:
            return {
                "success": True,
                "message": f"Status cleared for {member_identifier}"
            }
        else:
            return {
                "success": False,
                "message": f"No status found for {member_identifier}"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear member status: {str(e)}"
        )