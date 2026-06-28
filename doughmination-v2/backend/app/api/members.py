"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Member API endpoints
Handles member listing, details, and tags
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, Body

from app.services.pluralkit import get_members
from app.services.tag_service import (
    get_member_tags, update_member_tags, add_member_tag,
    remove_member_tag, enrich_members_with_tags
)
from app.services.status_service import enrich_members_with_status
from app.dependencies.auth import get_admin_user
from app.utils.cache import set_in_cache

router = APIRouter()

@router.get("/members")
async def list_members():
    """Get all members with tags and status information"""
    try:
        # Get members from PluralKit
        members_data = await get_members()
        
        # Enrich with tags
        members_with_tags = enrich_members_with_tags(members_data)
        
        # Enrich with status information
        members_with_status = enrich_members_with_status(members_with_tags)
        
        return members_with_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch members: {str(e)}"
        )

@router.get("/member/{member_id}")
async def member_detail(member_id: str):
    """Get details for a specific member"""
    try:
        members = await get_members()
        
        # Find member by ID or name
        member = None
        for m in members:
            if m["id"] == member_id or m["name"].lower() == member_id.lower():
                member = m
                break
        
        if not member:
            raise HTTPException(
                status_code=404,
                detail="Member not found"
            )
        
        # Enrich with tags and status
        member_with_tags = enrich_members_with_tags([member])[0]
        member_with_status = enrich_members_with_status([member_with_tags])[0]
        
        return member_with_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch member details: {str(e)}"
        )

# ============================================================================
# MEMBER TAGS ENDPOINTS
# ============================================================================

@router.get("/member-tags")
async def list_member_tags(user=Depends(get_admin_user)):
    """Get all member tag assignments (admin only)"""
    try:
        member_tags = get_member_tags()
        return {
            "status": "success",
            "member_tags": member_tags
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch member tags: {str(e)}"
        )

@router.post("/member-tags/{member_identifier}")
async def update_member_tag_list(
    member_identifier: str,
    tags: List[str] = Body(...),
    user=Depends(get_admin_user)
):
    """Update the complete tag list for a member (admin only)"""
    try:
        success = update_member_tags(member_identifier, tags)
        
        if success:
            # Clear member cache to reflect changes
            set_in_cache("members_raw", None, 0)
            
            return {
                "status": "success",
                "message": f"Updated tags for {member_identifier}",
                "tags": tags
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update member tags"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update member tags: {str(e)}"
        )

@router.post("/member-tags/{member_identifier}/add")
async def add_single_member_tag(
    member_identifier: str,
    tag: str = Body(..., embed=True),
    user=Depends(get_admin_user)
):
    """Add a single tag to a member (admin only)"""
    try:
        success = add_member_tag(member_identifier, tag)
        
        if success:
            # Clear member cache
            set_in_cache("members_raw", None, 0)
            
            return {
                "status": "success",
                "message": f"Added tag '{tag}' to {member_identifier}"
            }
        else:
            return {
                "status": "info",
                "message": f"Tag '{tag}' already exists for {member_identifier}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add member tag: {str(e)}"
        )

@router.delete("/member-tags/{member_identifier}/{tag}")
async def remove_single_member_tag(
    member_identifier: str,
    tag: str,
    user=Depends(get_admin_user)
):
    """Remove a single tag from a member (admin only)"""
    try:
        success = remove_member_tag(member_identifier, tag)
        
        if success:
            # Clear member cache
            set_in_cache("members_raw", None, 0)
            
            return {
                "status": "success",
                "message": f"Removed tag '{tag}' from {member_identifier}"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Tag '{tag}' not found for {member_identifier}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove member tag: {str(e)}"
        )
