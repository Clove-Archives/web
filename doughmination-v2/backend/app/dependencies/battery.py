"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Battery API authentication dependency
Simple header-based static key check, designed to be trivially callable from
Apple Shortcuts ("Get Contents of URL") and curl.
"""

from typing import Optional
from fastapi import Header, HTTPException, status

from app.services.battery_key_service import verify_battery_key


async def verify_battery_access(
    x_battery_key: Optional[str] = Header(None, alias="X-Battery-Key")
) -> bool:
    """
    Verify battery API access via the X-Battery-Key header.

    Raises:
        HTTPException: 401 if the header is missing or the key is invalid.
    """
    if not x_battery_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Battery-Key header",
        )

    if not verify_battery_key(x_battery_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid battery API key",
        )

    return True
