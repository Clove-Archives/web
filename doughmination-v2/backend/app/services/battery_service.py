"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Battery level service
Stores the latest known battery level for each device.

Storage is a single JSON file keyed by device name, each value:
    { "level": <int 0-100>, "updated_at": <ISO 8601 UTC> }

Only the latest value per device is kept (no history). Adding history would
be a small change: make each value a list and append instead of overwrite.
"""

import json
from typing import Dict, Optional
from datetime import datetime, timezone

from app.core.config import BATTERY_LEVELS_FILE


def get_all_levels() -> Dict[str, Dict]:
    """Get the latest battery level for all devices"""
    if not BATTERY_LEVELS_FILE.exists():
        return {}

    with open(BATTERY_LEVELS_FILE, "r") as f:
        return json.load(f)


def save_all_levels(levels: Dict[str, Dict]):
    """Save all battery levels to file"""
    with open(BATTERY_LEVELS_FILE, "w") as f:
        json.dump(levels, f, indent=2)


def get_device_level(device: str) -> Optional[Dict]:
    """Get the latest battery level for a single device, or None"""
    return get_all_levels().get(device)


def set_device_level(device: str, level: int) -> Dict:
    """
    Store the latest battery level for a device.

    Args:
        device: Arbitrary device name (e.g. "iphone", "macbook")
        level: Battery percentage, 0-100

    Returns:
        The stored record, including the device name.
    """
    levels = get_all_levels()

    record = {
        "level": level,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    levels[device] = record
    save_all_levels(levels)

    return {"device": device, **record}


def initialize_battery_storage():
    """Initialize the battery levels storage file if it doesn't exist"""
    if not BATTERY_LEVELS_FILE.exists():
        save_all_levels({})
        print("Initialized battery levels storage")
