"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Data models package
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

# Import user models
from app.models.user import (
    User,
    UserCreate,
    UserResponse,
    UserUpdate,
    LoginRequest
)

# Mental state model
class MentalState(BaseModel):
    """Mental state tracking model"""
    level: str  # safe, unstable, idealizing, self-harming, highly at risk
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

# System info model
class SystemInfo(BaseModel):
    """PluralKit system information"""
    id: str
    name: str
    description: Optional[str]
    tag: Optional[str]
    mental_state: Optional[MentalState] = None

# Bot models
class TokenRegenerateResponse(BaseModel):
    """Response for bot token regeneration"""
    success: bool
    message: str
    new_token: str

class HealthResponse(BaseModel):
    """Bot health check response"""
    status: str
    message: str
    authenticated: bool

class FronterUpdateRequest(BaseModel):
    """Request to update a single fronter"""
    member_id: str

class MultiSwitchRequest(BaseModel):
    """Request to switch multiple fronters"""
    member_ids: List[str]

class FronterUpdateResponse(BaseModel):
    """Response from fronter update"""
    success: bool
    message: str
    fronters: list

class MultiSwitchResponse(BaseModel):
    """Response from multi-switch"""
    status: str
    message: str
    fronters: list
    count: int

# Battery models
class BatteryLevel(BaseModel):
    """Latest battery level for a single device"""
    device: str
    level: int = Field(..., ge=0, le=100)
    updated_at: datetime

class BatteryUpdateResponse(BaseModel):
    """Response after storing a battery level"""
    success: bool
    device: str
    level: int
    updated_at: datetime

# Export all
__all__ = [
    'User',
    'UserCreate',
    'UserResponse',
    'UserUpdate',
    'LoginRequest',
    'MentalState',
    'SystemInfo',
    'TokenRegenerateResponse',
    'HealthResponse',
    'FronterUpdateRequest',
    'MultiSwitchRequest',
    'FronterUpdateResponse',
    'MultiSwitchResponse',
    'BatteryLevel',
    'BatteryUpdateResponse',
]