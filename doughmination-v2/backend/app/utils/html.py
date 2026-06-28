"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
HTML utility functions
"""

from typing import Optional

def escape_html(text: str) -> str:
    """
    Escape HTML special characters
    
    Args:
        text: Text to escape
    
    Returns:
        Escaped text safe for HTML
    """
    if not text:
        return ""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;'))

def normalize_hex(color: Optional[str], default: str = "#FF69B4") -> str:
    """
    Normalize hex color code
    
    Args:
        color: Color string (with or without #)
        default: Default color if input is invalid
    
    Returns:
        Normalized hex color (e.g., #FF69B4)
    """
    if not isinstance(color, str) or not color:
        return default
    
    c = color.lstrip("#")
    
    # Validate hex format
    if len(c) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in c):
        return f"#{c.upper()}"
    
    return default