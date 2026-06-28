"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
User data models
"""

from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    """Internal user model with password hash"""
    id: str
    username: str
    password_hash: str
    display_name: Optional[str] = None
    is_admin: bool = False
    is_owner: bool = False
    is_pet: bool = False
    avatar_url: Optional[str] = None

class UserCreate(BaseModel):
    """Model for creating a new user"""
    username: str
    password: str
    display_name: Optional[str] = None
    is_admin: bool = False
    is_pet: bool = False

class UserResponse(BaseModel):
    """Public user model (no password hash)"""
    id: str
    username: str
    display_name: Optional[str] = None
    is_admin: bool = False
    is_owner: bool = False
    is_pet: bool = False
    avatar_url: Optional[str] = None

class UserUpdate(BaseModel):
    """Model for updating user information"""
    display_name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    avatar_url: Optional[str] = None
    is_admin: Optional[bool] = None
    is_pet: Optional[bool] = None

class LoginRequest(BaseModel):
    """Model for login with Turnstile"""
    username: str
    password: str
    turnstile_token: str