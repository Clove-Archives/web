"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Metrics/analytics API endpoints
Provides fronting time and switch frequency statistics
"""

from fastapi import APIRouter, HTTPException, Depends

from app.services.metrics_service import (
    get_fronting_time_metrics,
    get_switch_frequency_metrics
)
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/metrics/fronting-time")
async def fronting_time_metrics(
    days: int = 30,
    user=Depends(get_current_user)
):
    """Get fronting time metrics for each member over different timeframes"""
    try:
        metrics = await get_fronting_time_metrics(days)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch fronting metrics: {str(e)}"
        )

@router.get("/metrics/switch-frequency")
async def switch_frequency_metrics(
    days: int = 30,
    user=Depends(get_current_user)
):
    """Get switch frequency metrics over different timeframes"""
    try:
        metrics = await get_switch_frequency_metrics(days)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch switch frequency metrics: {str(e)}"
        )