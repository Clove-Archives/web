"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
User management API endpoints
Handles user CRUD operations and avatar uploads
"""

import os
import uuid
import aiofiles
from typing import List
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, status

from app.models import User, UserCreate, UserResponse, UserUpdate
from app.services.user_service import (
    get_users, create_user, update_user, delete_user, get_user_by_id
)
from app.dependencies.auth import get_current_user, get_admin_user
from app.core.config import (
    DATA_DIR, MAX_AVATAR_SIZE, ALLOWED_AVATAR_EXTENSIONS, BASE_URL
)

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: User = Depends(get_admin_user)):
    """Get all users (admin only)"""
    users = get_users()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            is_admin=user.is_admin,
            is_owner=user.is_owner,
            is_pet=user.is_pet,
            avatar_url=getattr(user, 'avatar_url', None)
        )
        for user in users
    ]

@router.post("/users", response_model=UserResponse)
async def add_user(
    user_create: UserCreate,
    current_user: User = Depends(get_admin_user)
):
    """Create a new user (admin only)"""
    try:
        new_user = create_user(user_create, requesting_user=current_user)
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            display_name=new_user.display_name,
            is_admin=new_user.is_admin,
            is_owner=new_user.is_owner,
            is_pet=new_user.is_pet,
            avatar_url=getattr(new_user, 'avatar_url', None)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user information (admin or self)"""
    # Only admins or the user themselves can update their info
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    try:
        updated_user = update_user(user_id, user_update, requesting_user=current_user)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            display_name=updated_user.display_name,
            is_admin=updated_user.is_admin,
            is_owner=updated_user.is_owner,
            is_pet=updated_user.is_pet,
            avatar_url=getattr(updated_user, 'avatar_url', None)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.delete("/users/{user_id}")
async def remove_user(
    user_id: str,
    current_user: User = Depends(get_admin_user)
):
    """Delete a user (admin only)"""
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        success = delete_user(user_id, requesting_user=current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deleted successfully"}
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

@router.post("/users/{user_id}/avatar")
async def upload_user_avatar(
    user_id: str,
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload user avatar (admin or self)"""
    # Only admins or the user themselves can update their avatar
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Verify user exists
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate file extension
    _, file_ext = os.path.splitext(avatar.filename)
    file_ext = file_ext.lower()
    
    if file_ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_AVATAR_EXTENSIONS)}"
        )
    
    # Validate file size
    content_length = int(avatar.headers.get("content-length", 0))
    if content_length > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the limit of {MAX_AVATAR_SIZE // (1024 * 1024)}MB"
        )
    
    try:
        # Read file content
        contents = await avatar.read()
        file_size = len(contents)
        
        # Double-check file size
        if file_size > MAX_AVATAR_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the limit of {MAX_AVATAR_SIZE // (1024 * 1024)}MB"
            )
        
        # Generate unique filename
        unique_filename = f"{user_id}_{uuid.uuid4()}{file_ext}"
        file_path = DATA_DIR / unique_filename
        
        # Remove old avatar if exists
        if hasattr(user, 'avatar_url') and user.avatar_url:
            try:
                old_filename = user.avatar_url.split("/")[-1]
                old_path = DATA_DIR / old_filename
                if old_path.exists():
                    old_path.unlink()
            except Exception as e:
                print(f"Error removing old avatar: {e}")
        
        # Save new file
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(contents)
        
        # Construct avatar URL
        avatar_url = f"{BASE_URL}/avatars/{unique_filename}"
        
        # Update user with avatar URL
        user_update = UserUpdate(avatar_url=avatar_url)
        updated_user = update_user(user_id, user_update, requesting_user=current_user)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user with avatar URL"
            )
        
        return {"success": True, "avatar_url": avatar_url}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading avatar: {str(e)}"
        )