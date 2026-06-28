"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Member tagging service
Manages tags/categories for system members
"""

import json
from typing import List, Dict
from app.core.config import MEMBER_TAGS_FILE

# Default member tag assignments
DEFAULT_MEMBER_TAGS = {
    "Jinx": ["Arcane"],
    "Vi": ["Arcane"],
    "Onyx": ["Cat"],
    "Pyzer": ["Cat"],
    "Pyzen": ["Cat"],
    "JS": ["Cyberpunk"],
    "V": ["Cyberpunk"],
    "Judy": ["Cyberpunk"],
    "Marin": ["DUD"],
    "Roxy": ["FNAF"],
    "Catrin": ["Fortnite"],
    "Hope": ["Fortnite"],
    "Meg": ["Fortnite"],
    "02": ["Franxx"],
    "C1": ["Host"],
    "Cleo": ["Host"],
    "Cwove": ["Host"],
    "abby": ["KPDH"],
    "baby": ["KPDH"],
    "Bobby": ["KPDH"],
    "jinu": ["KPDH"],
    "Mira": ["KPDH"],
    "mystery": ["KPDH"],
    "romance": ["KPDH"],
    "Rumi": ["KPDH"],
    "Zoey": ["KPDH"],
    "Dashie": ["MLP"],
    "D.Va": ["Overwatch"],
    "Tracer": ["Overwatch"],
    "Astra": ["Valorant"],
    "C2": ["Valorant"],
    "Cypher": ["Valorant"],
    "Deadlock": ["Valorant"],
    "Fade": ["Valorant"],
    "Jett": ["Valorant"],
    "KJ": ["Valorant"],
    "Neon": ["Valorant"],
    "Raze": ["Valorant"],
    "Reyna": ["Valorant"],
    "Sage": ["Valorant"],
    "Viper": ["Valorant"],
    "Vyse": ["Valorant"],
    "CMiku": ["Vocaloids"],
    "HMiku": ["Vocaloids"],
    "SMiku": ["Vocaloids"],
    "Anby": ["ZZZ"],
    "Belle": ["ZZZ"]
}

def get_member_tags() -> Dict[str, List[str]]:
    """Get all member tag assignments"""
    if not MEMBER_TAGS_FILE.exists():
        save_member_tags(DEFAULT_MEMBER_TAGS)
        return DEFAULT_MEMBER_TAGS.copy()
    
    with open(MEMBER_TAGS_FILE, "r") as f:
        return json.load(f)

def save_member_tags(member_tags: Dict[str, List[str]]):
    """Save member tags to file"""
    with open(MEMBER_TAGS_FILE, "w") as f:
        json.dump(member_tags, f, indent=2)

def get_member_tags_by_id(member_id: str, member_name: str) -> List[str]:
    """Get tags for a specific member by ID or name"""
    member_tags = get_member_tags()
    
    # Try by member name first
    if member_name in member_tags:
        return member_tags[member_name]
    
    # Then try by member ID
    if member_id in member_tags:
        return member_tags[member_id]
    
    return []

def update_member_tags(member_identifier: str, tags: List[str]) -> bool:
    """Update tags for a member (can use ID or name)"""
    member_tags = get_member_tags()
    member_tags[member_identifier] = tags
    save_member_tags(member_tags)
    return True

def add_member_tag(member_identifier: str, tag: str) -> bool:
    """Add a single tag to a member"""
    member_tags = get_member_tags()
    if member_identifier not in member_tags:
        member_tags[member_identifier] = []
    
    if tag not in member_tags[member_identifier]:
        member_tags[member_identifier].append(tag)
        save_member_tags(member_tags)
        return True
    
    return False

def remove_member_tag(member_identifier: str, tag: str) -> bool:
    """Remove a single tag from a member"""
    member_tags = get_member_tags()
    if member_identifier in member_tags and tag in member_tags[member_identifier]:
        member_tags[member_identifier].remove(tag)
        save_member_tags(member_tags)
        return True
    
    return False

def enrich_members_with_tags(members: List[Dict]) -> List[Dict]:
    """Add tag information to all members"""
    enriched_members = []
    
    for member in members:
        member_name = member.get("name", "")
        member_id = member.get("id", "")
        
        # Get tags for this member
        tags = get_member_tags_by_id(member_id, member_name)
        
        # Add tags to member data
        member_with_tags = {**member, "tags": tags}
        enriched_members.append(member_with_tags)
    
    return enriched_members

def initialize_default_tags():
    """Initialize default member tags if they don't exist"""
    if not MEMBER_TAGS_FILE.exists():
        save_member_tags(DEFAULT_MEMBER_TAGS)
        print("Initialized default member tags")