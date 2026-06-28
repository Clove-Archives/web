"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Mental state service
Manages system mental state tracking
"""

import json
from datetime import datetime, timezone
from typing import Optional
from app.core.config import MENTAL_STATE_FILE
from app.models import MentalState

def get_mental_state() -> MentalState:
    """Get current mental state from storage"""
    try:
        if MENTAL_STATE_FILE.exists():
            with open(MENTAL_STATE_FILE, "r") as f:
                state_data = json.load(f)
                # Convert the string back to datetime
                state_data["updated_at"] = datetime.fromisoformat(state_data["updated_at"])
                return MentalState(**state_data)
        else:
            # Return default state
            return MentalState(
                level="safe",
                updated_at=datetime.now(timezone.utc),
                notes=None
            )
    except Exception as e:
        print(f"Error loading mental state: {e}")
        return MentalState(
            level="safe",
            updated_at=datetime.now(timezone.utc),
            notes=None
        )

def save_mental_state(state: MentalState) -> bool:
    """Save mental state to storage"""
    try:
        state_data = state.dict()
        state_data["updated_at"] = state_data["updated_at"].isoformat()
        
        with open(MENTAL_STATE_FILE, "w") as f:
            json.dump(state_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving mental state: {e}")
        return False

def update_mental_state(level: str, notes: Optional[str] = None) -> MentalState:
    """
    Update mental state with new level and notes
    
    Args:
        level: Mental state level (safe, unstable, idealizing, self-harming, highly at risk)
        notes: Optional notes about the state
    
    Returns:
        Updated mental state
    """
    state = MentalState(
        level=level,
        updated_at=datetime.now(timezone.utc),
        notes=notes
    )
    
    save_mental_state(state)
    return state