"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
User management service
Handles user CRUD operations, authentication, and permissions
"""

import json
import uuid
import re
from typing import List, Optional
from pathlib import Path

from app.models import User, UserCreate, UserUpdate
from app.core.config import USERS_FILE, ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_DISPLAY_NAME
from app.core.security import hash_password, verify_password

def get_owner_username() -> str:
    """Get the owner username from configuration"""
    return ADMIN_USERNAME

def is_owner_username(username: str) -> bool:
    """Check if a username matches the owner username"""
    return username.lower() == get_owner_username().lower()

def get_users() -> List[User]:
    """Get all users from storage"""
    if not USERS_FILE.exists():
        return []
    
    with open(USERS_FILE, "r") as f:
        users_data = json.load(f)
    
    users = []
    for user_dict in users_data:
        # Handle migration from old format
        if 'is_owner' not in user_dict:
            user_dict['is_owner'] = False
        if 'is_pet' not in user_dict:
            user_dict['is_pet'] = False
        
        # Force is_owner=True for the owner username
        if is_owner_username(user_dict.get('username', '')):
            user_dict['is_owner'] = True
            user_dict['is_admin'] = True
            user_dict['is_pet'] = True
        
        users.append(User(**user_dict))
    
    return users

def save_users(users: List[User]):
    """Save users to storage"""
    # Ensure owner always has full access
    owner_username = get_owner_username()
    for user in users:
        if is_owner_username(user.username):
            user.is_owner = True
            user.is_admin = True
            user.is_pet = True
    
    with open(USERS_FILE, "w") as f:
        json.dump([user.dict() for user in users], f, indent=2)

def get_user_by_username(username: str) -> Optional[User]:
    """Find a user by username (case-insensitive)"""
    users = get_users()
    for user in users:
        if user.username.lower() == username.lower():
            return user
    return None

def get_user_by_id(user_id: str) -> Optional[User]:
    """Find a user by ID"""
    users = get_users()
    for user in users:
        if user.id == user_id:
            return user
    return None

def create_user(user_create: UserCreate, requesting_user: Optional[User] = None) -> User:
    """
    Create a new user with owner protection
    
    Args:
        user_create: User creation data
        requesting_user: The user making the request (for permission checks)
    
    Returns:
        Created user
    
    Raises:
        ValueError: If username exists
        PermissionError: If trying to create owner or unauthorized action
    """
    users = get_users()
    
    # Check if username already exists
    if get_user_by_username(user_create.username):
        raise ValueError(f"Username '{user_create.username}' already exists")
    
    # BLOCK: Prevent creating owner username unless this is initial setup
    if is_owner_username(user_create.username) and requesting_user is not None:
        raise PermissionError("Cannot create user with owner username. Owner account must be created via initial setup.")
    
    # Determine permissions
    if is_owner_username(user_create.username):
        # This is the initial owner creation
        is_owner = True
        is_admin = True
        is_pet = False
    else:
        # Regular user creation
        is_owner = False
        is_admin = user_create.is_admin
        is_pet = user_create.is_pet
    
    # Create new user
    new_user = User(
        id=str(uuid.uuid4()),
        username=user_create.username,
        password_hash=hash_password(user_create.password),
        display_name=user_create.display_name,
        is_admin=is_admin,
        is_owner=is_owner,
        is_pet=is_pet,
        avatar_url=None
    )
    
    users.append(new_user)
    save_users(users)
    
    return new_user

def update_user(user_id: str, user_update: UserUpdate, requesting_user: Optional[User] = None) -> Optional[User]:
    """
    Update a user with owner protection
    
    Args:
        user_id: ID of user to update
        user_update: Update data
        requesting_user: The user making the request
    
    Returns:
        Updated user or None if not found
    
    Raises:
        PermissionError: If unauthorized changes attempted
        ValueError: If current password is incorrect
    """
    users = get_users()
    
    for i, user in enumerate(users):
        if user.id == user_id:
            # BLOCK: Prevent changing owner's is_owner or is_admin flags
            if user.is_owner:
                if user_update.is_admin is False:
                    raise PermissionError("Cannot remove admin privileges from owner")
            
            # BLOCK: Only owner can modify admin accounts (except themselves)
            if requesting_user and user.is_admin and requesting_user.id != user.id:
                if not requesting_user.is_owner:
                    raise PermissionError("Only the owner can modify admin accounts")
            
            # Verify current password if attempting to change password
            if user_update.current_password and user_update.new_password:
                if not verify_password(user_update.current_password, user.password_hash):
                    raise ValueError("Current password is incorrect")
                
                password_hash = hash_password(user_update.new_password)
            else:
                password_hash = user.password_hash
            
            # Determine new permissions
            new_is_owner = is_owner_username(user.username)
            
            if new_is_owner:
                new_is_admin = True
            elif user_update.is_admin is not None:
                new_is_admin = user_update.is_admin
            else:
                new_is_admin = user.is_admin
            
            if user_update.is_pet is not None:
                new_is_pet = user_update.is_pet
            else:
                new_is_pet = user.is_pet
            
            # Update the user
            updated_user = User(
                id=user.id,
                username=user.username,
                password_hash=password_hash,
                display_name=user_update.display_name if user_update.display_name is not None else user.display_name,
                is_admin=new_is_admin,
                is_owner=new_is_owner,
                is_pet=new_is_pet,
                avatar_url=user_update.avatar_url if user_update.avatar_url is not None else getattr(user, 'avatar_url', None)
            )
            users[i] = updated_user
            save_users(users)
            return updated_user
    
    return None

def delete_user(user_id: str, requesting_user: Optional[User] = None) -> bool:
    """
    Delete a user with owner protection
    
    Args:
        user_id: ID of user to delete
        requesting_user: The user making the request
    
    Returns:
        True if deleted, False if not found
    
    Raises:
        PermissionError: If trying to delete owner or unauthorized
    """
    users = get_users()
    
    # Find the user to delete
    user_to_delete = None
    for user in users:
        if user.id == user_id:
            user_to_delete = user
            break
    
    if not user_to_delete:
        return False
    
    # BLOCK: Prevent deleting the owner
    if user_to_delete.is_owner:
        raise PermissionError("Cannot delete the owner account")
    
    # BLOCK: Only owner can delete admins
    if requesting_user and user_to_delete.is_admin:
        if not requesting_user.is_owner:
            raise PermissionError("Only the owner can delete admin accounts")
    
    # Perform deletion
    original_count = len(users)
    users = [user for user in users if user.id != user_id]
    
    if len(users) < original_count:
        save_users(users)
        return True
    
    return False

def verify_user(username: str, password: str) -> Optional[User]:
    """Verify user credentials"""
    user = get_user_by_username(username)
    if user and verify_password(password, user.password_hash):
        return user
    return None

def initialize_admin_user():
    """Creates the admin user from environment variables if no users exist"""
    users = get_users()
    if not users:
        admin_username = ADMIN_USERNAME
        admin_password_or_hash = ADMIN_PASSWORD
        admin_display_name = ADMIN_DISPLAY_NAME
        
        if not admin_password_or_hash:
            print("Warning: No ADMIN_PASSWORD set in environment. Using default password 'admin'")
            admin_password_or_hash = "admin"
        
        try:
            # Check if the password is already a bcrypt hash
            is_hash = bool(re.match(r'^\$2[aby]\$\d+\$.+', admin_password_or_hash))
            
            if is_hash:
                # If it's already a hash, create the user directly
                new_user = User(
                    id=str(uuid.uuid4()),
                    username=admin_username,
                    password_hash=admin_password_or_hash,
                    display_name=admin_display_name,
                    is_admin=True,
                    is_owner=True,
                    is_pet=False,
                    avatar_url=None
                )
                users.append(new_user)
                save_users(users)
                print(f"Created owner user with provided hash: {admin_username} (Display name: {admin_display_name})")
            else:
                # If it's not a hash, create the user normally
                create_user(UserCreate(
                    username=admin_username,
                    password=admin_password_or_hash,
                    display_name=admin_display_name,
                    is_admin=True,
                    is_pet=False
                ))
                print(f"Created owner user: {admin_username} (Display name: {admin_display_name})")
        except Exception as e:
            print(f"Error creating owner user: {e}")