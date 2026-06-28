"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
PluralKit API integration service
Handles all interactions with the PluralKit API
"""

import httpx
from typing import List, Dict, Any
from app.core.config import PLURALKIT_BASE_URL, get_pluralkit_headers, CACHE_TTL
from app.utils.cache import get_from_cache, set_in_cache

# Special member display names
SPECIAL_DISPLAY_NAMES = {
    "answer": "Answer Machine",
    "system": "Unsure",
    "sleeping": "I am sleeping"
}

async def get_system() -> Dict[str, Any]:
    """Get system information from PluralKit"""
    cache_key = "system"
    if (cached := get_from_cache(cache_key)):
        return cached
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PLURALKIT_BASE_URL}/systems/@me",
            headers=get_pluralkit_headers()
        )
        resp.raise_for_status()
        data = resp.json()
        set_in_cache(cache_key, data, CACHE_TTL)
        return data

async def get_members() -> List[Dict[str, Any]]:
    """Get all system members from PluralKit"""
    cache_key = "members"
    if (cached := get_from_cache(cache_key)):
        return cached
    
    # Get raw members from API
    base_cache_key = "members_raw"
    if not (cached_raw := get_from_cache(base_cache_key)):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{PLURALKIT_BASE_URL}/systems/@me/members",
                headers=get_pluralkit_headers()
            )
            resp.raise_for_status()
            cached_raw = resp.json()
            set_in_cache(base_cache_key, cached_raw, CACHE_TTL)
    
    # Process special members
    processed_members = []
    for member in cached_raw:
        member_name = member.get("name")
        
        if member_name in SPECIAL_DISPLAY_NAMES:
            special_member = {
                **member,
                "display_name": SPECIAL_DISPLAY_NAMES[member_name],
                "is_special": True,
                "original_name": member_name
            }
            processed_members.append(special_member)
        else:
            processed_members.append(member)
    
    set_in_cache(cache_key, processed_members, CACHE_TTL)
    return processed_members

async def get_fronters() -> Dict[str, Any]:
    """Get current fronters from PluralKit"""
    cache_key = "fronters"
    if (cached := get_from_cache(cache_key)):
        return cached
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PLURALKIT_BASE_URL}/systems/@me/fronters",
            headers=get_pluralkit_headers()
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Process special members in fronters
        if "members" in data:
            all_members = await get_members()
            
            processed_fronters = []
            for member in data["members"]:
                # Find processed member data
                processed_member = next(
                    (m for m in all_members if m.get("id") == member.get("id")),
                    member
                )
                processed_fronters.append(processed_member)
            
            data["members"] = processed_fronters
        
        set_in_cache(cache_key, data, CACHE_TTL)
        return data

async def set_front(member_ids: List[str]) -> Any:
    """
    Set the current front to the provided list of member IDs
    
    Args:
        member_ids: List of member IDs to set as fronting
    
    Returns:
        Response from PluralKit API (or None)
    """
    # Clear fronters cache
    set_in_cache("fronters", None, 0)
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PLURALKIT_BASE_URL}/systems/@me/switches",
            headers=get_pluralkit_headers(),
            json={"members": member_ids}
        )
        
        if resp.status_code not in (200, 204):
            raise Exception(f"Failed to set front: {resp.status_code} - {resp.text}")
        
        return resp.json() if resp.content else None

async def get_switches(limit: int = 1000) -> List[Dict[str, Any]]:
    """Get recent switches from PluralKit"""
    cache_key = f"switches_{limit}"
    if (cached := get_from_cache(cache_key)):
        return cached
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PLURALKIT_BASE_URL}/systems/@me/switches?limit={limit}",
            headers=get_pluralkit_headers()
        )
        resp.raise_for_status()
        data = resp.json()
        set_in_cache(cache_key, data, CACHE_TTL)
        return data