"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Battery level API endpoints
Devices POST their current battery percentage; clients GET the latest known
value(s). Latest-value-per-device only (no history).
"""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models import BatteryLevel, BatteryUpdateResponse
from app.services.battery_service import (
    get_all_levels,
    get_device_level,
    set_device_level,
)
from app.dependencies.battery import verify_battery_access

router = APIRouter(prefix="/api/battery")


@router.post("", response_model=BatteryUpdateResponse)
async def update_battery(
    device: str = Query(..., min_length=1, max_length=64, description="Device name, e.g. 'iphone'"),
    level: int = Query(..., ge=0, le=100, description="Battery percentage, 0-100"),
    authenticated: bool = Depends(verify_battery_access),
):
    """
    Store the latest battery level for a device.

    Example: POST /api/battery?device=iphone&level=25
    """
    record = set_device_level(device, level)
    return BatteryUpdateResponse(success=True, **record)


@router.get("", response_model=Dict[str, BatteryLevel])
async def get_all_battery():
    """Get the latest battery level for all known devices. (Public)"""
    levels = get_all_levels()
    return {device: {"device": device, **record} for device, record in levels.items()}


@router.get("/{device}", response_model=BatteryLevel)
async def get_battery(device: str):
    """Get the latest battery level for a single device. (Public)"""
    record = get_device_level(device)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No battery level recorded for device '{device}'",
        )
    return {"device": device, **record}
