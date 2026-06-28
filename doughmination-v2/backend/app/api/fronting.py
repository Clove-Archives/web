"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Fronting control API endpoints
Handles switching and fronter management
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, Depends, Body

from app.services.pluralkit import get_fronters, set_front, get_members
from app.services.tag_service import enrich_members_with_tags
from app.services.status_service import enrich_members_with_status
from app.dependencies.auth import get_current_user
from app.core.websocket import broadcast_fronting_update

router = APIRouter()

@router.get("/fronters")
async def list_fronters():
    """Get current fronters with tags and status"""
    try:
        fronters_data = await get_fronters()
        
        # Enrich fronters with tags and status
        if "members" in fronters_data:
            members_with_tags = enrich_members_with_tags(fronters_data["members"])
            fronters_data["members"] = enrich_members_with_status(members_with_tags)
        
        return fronters_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch fronters: {str(e)}"
        )

@router.post("/switch")
async def switch_front(
    request: Request,
    user=Depends(get_current_user)
):
    """Switch fronters (multiple members)"""
    try:
        body = await request.json()
        member_ids = body.get("members", [])

        if not isinstance(member_ids, list):
            raise HTTPException(
                status_code=400,
                detail="'members' must be a list of member IDs"
            )

        await set_front(member_ids)
        
        # Broadcast the fronting update
        fronters_data = await get_fronters()
        await broadcast_fronting_update(fronters_data)
        
        return {"status": "success", "message": "Front updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/switch_front")
async def switch_single_front(
    request: Request,
    user=Depends(get_current_user)
):
    """Switch to a single fronter"""
    try:
        body = await request.json()
        member_id = body.get("member_id")
        
        if not member_id:
            raise HTTPException(
                status_code=400,
                detail="member_id is required"
            )

        result = await set_front([member_id])

        # Broadcast the update
        fronters_data = await get_fronters()
        await broadcast_fronting_update(fronters_data)

        return {"success": True, "message": "Front updated", "data": result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to switch front: {str(e)}"
        )

@router.post("/multi_switch")
async def switch_multiple_fronters(
    data: Dict[str, Any] = Body(...),
    user=Depends(get_current_user)
):
    """
    Switch to multiple fronters at once
    Alternative to /switch with more detailed feedback
    """
    try:
        member_ids = data.get("member_ids", [])
        
        if not isinstance(member_ids, list):
            raise HTTPException(
                status_code=400,
                detail="'member_ids' must be a list"
            )
        
        # Get members to show their names in the response
        all_members = await get_members()
        switching_members = []
        
        for member_id in member_ids:
            for member in all_members:
                if member.get("id") == member_id:
                    switching_members.append({
                        "id": member.get("id"),
                        "name": member.get("name"),
                        "display_name": member.get("display_name", member.get("name"))
                    })
                    break
        
        # Switch the fronters
        await set_front(member_ids)
        
        # Broadcast the fronting update
        fronters_data = await get_fronters()
        await broadcast_fronting_update(fronters_data)
        
        # Return detailed information
        return {
            "status": "success",
            "message": "Fronters updated successfully",
            "fronters": switching_members,
            "count": len(switching_members)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )