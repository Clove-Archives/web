"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Bot token service
Manages secure access tokens for Discord bot integration
"""

import json
import secrets
from typing import Optional
from datetime import datetime, timezone
from app.core.config import BOT_TOKEN_FILE

def generate_bot_token() -> str:
    """Generate a secure random token for bot access"""
    return secrets.token_urlsafe(32)

def get_bot_token() -> Optional[str]:
    """Get the current bot access token"""
    if not BOT_TOKEN_FILE.exists():
        return None
    
    try:
        with open(BOT_TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data.get("token")
    except Exception as e:
        print(f"Error reading bot token: {e}")
        return None

def save_bot_token(token: str):
    """Save the bot access token to file"""
    data = {
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }
    
    with open(BOT_TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def initialize_bot_token() -> str:
    """Initialize bot token on startup, creating new one if doesn't exist"""
    existing_token = get_bot_token()
    
    if existing_token:
        print(f"✓ Bot access token loaded from file")
        print(f"  Token: {existing_token}")
        return existing_token
    
    # Generate new token
    new_token = generate_bot_token()
    save_bot_token(new_token)
    
    print("=" * 60)
    print("NEW BOT ACCESS TOKEN GENERATED")
    print("=" * 60)
    print(f"Token: {new_token}")
    print()
    print("IMPORTANT: Save this token to your Discord bot's .env file as:")
    print(f"DOUGH_API_TOKEN={new_token}")
    print("=" * 60)
    
    return new_token

def regenerate_bot_token() -> str:
    """Regenerate the bot access token (effectively terminating the old one)"""
    new_token = generate_bot_token()
    save_bot_token(new_token)
    
    print("=" * 60)
    print("BOT ACCESS TOKEN REGENERATED")
    print("=" * 60)
    print(f"New Token: {new_token}")
    print()
    print("IMPORTANT: Update your Discord bot's .env file with the new token:")
    print(f"DOUGH_API_TOKEN={new_token}")
    print("=" * 60)
    
    return new_token

def verify_bot_token(provided_token: str) -> bool:
    """Verify if the provided token matches the current bot token"""
    current_token = get_bot_token()
    
    if not current_token:
        return False
    
    # Constant-time comparison to prevent timing attacks
    return secrets.compare_digest(current_token, provided_token)