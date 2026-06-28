"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
System information API endpoints
Handles system info and mental state
"""

from fastapi import APIRouter, HTTPException, Depends

from app.models import MentalState
from app.services.pluralkit import get_system
from app.services.mental_state_service import get_mental_state, save_mental_state
from app.dependencies.auth import get_admin_user
from app.core.websocket import broadcast_mental_state_update

router = APIRouter()

@router.get("/system")
async def system_info():
    """Get PluralKit system information with mental state"""
    try:
        # Get system data from PluralKit
        system_data = await get_system()
        
        # Get mental state
        mental_state = get_mental_state()
        
        # Add mental state to system data
        system_data["mental_state"] = mental_state.dict()
        
        return system_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch system info: {str(e)}"
        )

@router.get("/mental-state")
async def get_mental_state_endpoint():
    """Get current mental state"""
    try:
        state = get_mental_state()
        return state
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch mental state: {str(e)}"
        )

@router.post("/mental-state")
async def update_mental_state_endpoint(
    state: MentalState,
    user=Depends(get_admin_user)
):
    """Update mental state (admin only)"""
    try:
        success = save_mental_state(state)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to save mental state"
            )
        
        # Broadcast the mental state update
        state_data = state.dict()
        state_data["updated_at"] = state_data["updated_at"].isoformat()
        await broadcast_mental_state_update(state_data)
        
        return {"success": True, "message": "Mental state updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update mental state: {str(e)}"
        )