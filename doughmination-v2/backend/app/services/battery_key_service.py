"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Battery API key service
Manages the static access key used by devices to report battery levels.

Behaviour mirrors bot_token_service: a key is generated on first boot,
persisted to a JSON file, and verified with a constant-time comparison.

An optional BATTERY_API_KEYS environment variable (comma-separated) takes
precedence if set, so multiple keys / externally-managed keys are possible
without code changes.
"""

import os
import json
import secrets
from typing import List, Optional
from datetime import datetime, timezone

from app.core.config import BATTERY_KEY_FILE


def _env_keys() -> List[str]:
    """Return keys from the BATTERY_API_KEYS env var, if any."""
    raw = os.getenv("BATTERY_API_KEYS", "")
    return [k.strip() for k in raw.split(",") if k.strip()]


def generate_battery_key() -> str:
    """Generate a secure random key for battery access"""
    return secrets.token_urlsafe(32)


def get_stored_key() -> Optional[str]:
    """Get the current battery access key from file"""
    if not BATTERY_KEY_FILE.exists():
        return None

    try:
        with open(BATTERY_KEY_FILE, "r") as f:
            data = json.load(f)
            return data.get("key")
    except Exception as e:
        print(f"Error reading battery key: {e}")
        return None


def save_battery_key(key: str):
    """Save the battery access key to file"""
    data = {
        "key": key,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }

    with open(BATTERY_KEY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_valid_keys() -> List[str]:
    """
    Return all keys currently accepted.
    Env-provided keys take precedence; otherwise the generated/stored key.
    """
    env = _env_keys()
    if env:
        return env

    stored = get_stored_key()
    return [stored] if stored else []


def initialize_battery_key() -> Optional[str]:
    """Initialize battery key on startup, creating one if it doesn't exist"""
    env = _env_keys()
    if env:
        print(f"✓ Battery API key(s) loaded from BATTERY_API_KEYS env ({len(env)} key(s))")
        return env[0]

    existing = get_stored_key()
    if existing:
        print("✓ Battery access key loaded from file")
        print(f"  Key: {existing}")
        return existing

    new_key = generate_battery_key()
    save_battery_key(new_key)

    print("=" * 60)
    print("NEW BATTERY ACCESS KEY GENERATED")
    print("=" * 60)
    print(f"Key: {new_key}")
    print()
    print("Send this as the 'X-Battery-Key' header from your devices.")
    print("=" * 60)

    return new_key


def regenerate_battery_key() -> str:
    """Regenerate the stored battery access key (invalidates the old one)"""
    new_key = generate_battery_key()
    save_battery_key(new_key)

    print("=" * 60)
    print("BATTERY ACCESS KEY REGENERATED")
    print("=" * 60)
    print(f"New Key: {new_key}")
    print("=" * 60)

    return new_key


def verify_battery_key(provided_key: str) -> bool:
    """Verify the provided key against any valid key (constant-time)"""
    if not provided_key:
        return False

    # Compare against every valid key with constant-time comparison.
    valid = False
    for key in get_valid_keys():
        if secrets.compare_digest(key, provided_key):
            valid = True
    return valid
