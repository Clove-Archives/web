"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Datetime utility functions
"""

import re
from datetime import datetime, timezone

def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string with proper timezone handling
    Handles various ISO 8601 formats and microsecond precision issues
    
    Args:
        timestamp_str: ISO 8601 timestamp string
    
    Returns:
        Timezone-aware datetime object
    
    Raises:
        ValueError: If timestamp cannot be parsed
    """
    try:
        # Handle Z timezone indicator
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        # Try direct parsing first
        try:
            dt = datetime.fromisoformat(timestamp_str)
        except ValueError:
            # Handle microsecond precision issues
            match = re.match(
                r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)(\+\d{2}:\d{2})',
                timestamp_str
            )
            if match:
                base = match.group(1)
                # Truncate microseconds to 6 digits
                if len(base.split('.')[-1]) > 6:
                    base = base.split('.')[0] + '.' + base.split('.')[-1][:6]
                timestamp_str = f"{base}{match.group(2)}"
                dt = datetime.fromisoformat(timestamp_str)
            else:
                # Try another approach for microsecond issues
                parts = timestamp_str.split('.')
                if len(parts) == 2 and '+' in parts[1]:
                    ms_part, tz_part = parts[1].split('+', 1)
                    if len(ms_part) > 6:
                        ms_part = ms_part[:6]
                    timestamp_str = f"{parts[0]}.{ms_part}+{tz_part}"
                    dt = datetime.fromisoformat(timestamp_str)
                else:
                    raise ValueError(f"Could not parse timestamp: {timestamp_str}")
        
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt
        
    except Exception as e:
        print(f"Error parsing timestamp {timestamp_str}: {str(e)}")
        raise