"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Admin utility API endpoints
Special administrative functions
"""

from fastapi import APIRouter, HTTPException, Depends

from app.dependencies.auth import get_admin_user
from app.core.websocket import broadcast_frontend_update

router = APIRouter()

@router.post("/admin/refresh")
async def admin_refresh(user=Depends(get_admin_user)):
    """Force refresh all connected clients (admin only)"""
    try:
        # Broadcast refresh command to all WebSocket clients
        await broadcast_frontend_update("force_refresh", {
            "message": "Admin initiated refresh"
        })
        
        return {"success": True, "message": "Refresh broadcast sent"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to broadcast refresh: {str(e)}"
        )