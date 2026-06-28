"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Metrics/analytics service
Calculates fronting time and switch frequency metrics
"""

import traceback
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from app.services.pluralkit import get_switches, get_members
from app.utils.datetime import parse_timestamp

async def get_fronting_time_metrics(days: int = 30) -> Dict[str, Any]:
    """Calculate fronting time metrics for each member"""
    try:
        print(f"Calculating fronting metrics for past {days} days")
        
        # Get switches
        switches = await get_switches(1000)
        print(f"Retrieved {len(switches)} switches")
        
        # Calculate cutoff time
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(days=days)
        
        # Get member details
        member_details = {}
        try:
            members = await get_members()
            for member in members:
                member_details[member["id"]] = {
                    "name": member["name"],
                    "display_name": member.get("display_name", member["name"]),
                    "avatar_url": member.get("avatar_url", None)
                }
        except Exception as e:
            print(f"Error fetching member details: {e}")
        
        # Filter and parse switches
        filtered_switches = []
        for switch in switches:
            try:
                timestamp = parse_timestamp(switch["timestamp"])
                if timestamp >= cutoff_time:
                    filtered_switches.append({
                        **switch,
                        "_parsed_timestamp": timestamp
                    })
            except Exception as e:
                print(f"Error parsing timestamp: {e}")
                continue
        
        print(f"Filtered to {len(filtered_switches)} switches")
        
        # Sort by timestamp
        filtered_switches.sort(key=lambda x: x["_parsed_timestamp"])
        
        if not filtered_switches:
            return {
                "total_time": 0,
                "members": {},
                "timeframes": {"24h": {}, "48h": {}, "5d": {}, "7d": {}, "30d": {}}
            }
        
        # Add virtual current switch
        current_members = filtered_switches[-1]["members"]
        filtered_switches.append({
            "timestamp": now.isoformat(),
            "members": current_members,
            "_parsed_timestamp": now
        })
        
        # Calculate fronting times
        fronting_times = {}
        total_time_seconds = 0
        
        for i in range(1, len(filtered_switches)):
            prev_switch = filtered_switches[i-1]
            curr_switch = filtered_switches[i]
            
            try:
                prev_time = prev_switch["_parsed_timestamp"]
                curr_time = curr_switch["_parsed_timestamp"]
                duration_seconds = (curr_time - prev_time).total_seconds()
                total_time_seconds += duration_seconds
                
                for member_id in prev_switch["members"]:
                    if member_id not in fronting_times:
                        fronting_times[member_id] = {
                            "total_seconds": 0,
                            "24h": 0, "48h": 0, "5d": 0, "7d": 0, "30d": 0
                        }
                    
                    fronting_times[member_id]["total_seconds"] += duration_seconds
                    
                    time_ago = (now - prev_time).total_seconds()
                    if time_ago <= 24 * 3600:
                        fronting_times[member_id]["24h"] += duration_seconds
                    if time_ago <= 48 * 3600:
                        fronting_times[member_id]["48h"] += duration_seconds
                    if time_ago <= 5 * 24 * 3600:
                        fronting_times[member_id]["5d"] += duration_seconds
                    if time_ago <= 7 * 24 * 3600:
                        fronting_times[member_id]["7d"] += duration_seconds
                    if time_ago <= 30 * 24 * 3600:
                        fronting_times[member_id]["30d"] += duration_seconds
            except Exception as e:
                print(f"Error processing switch: {e}")
                continue
        
        # Format result
        result = {
            "total_time": total_time_seconds,
            "members": {},
            "timeframes": {"24h": {}, "48h": {}, "5d": {}, "7d": {}, "30d": {}}
        }
        
        for member_id, times in fronting_times.items():
            name = member_id
            display_name = member_id
            avatar_url = None
            
            if member_id in member_details:
                name = member_details[member_id]["name"]
                display_name = member_details[member_id]["display_name"]
                avatar_url = member_details[member_id]["avatar_url"]
            
            total_percent = (times["total_seconds"] / total_time_seconds * 100) if total_time_seconds > 0 else 0
            
            result["members"][member_id] = {
                "id": member_id,
                "name": name,
                "display_name": display_name,
                "avatar_url": avatar_url,
                "total_seconds": times["total_seconds"],
                "total_percent": total_percent,
                "24h": times["24h"],
                "48h": times["48h"],
                "5d": times["5d"],
                "7d": times["7d"],
                "30d": times["30d"]
            }
            
            for tf in ["24h", "48h", "5d", "7d", "30d"]:
                result["timeframes"][tf][member_id] = times[tf]
        
        print(f"Successfully calculated metrics for {len(result['members'])} members")
        return result
        
    except Exception as e:
        print(f"Error in get_fronting_time_metrics: {e}")
        print(traceback.format_exc())
        return {
            "total_time": 0,
            "members": {},
            "timeframes": {"24h": {}, "48h": {}, "5d": {}, "7d": {}, "30d": {}}
        }

async def get_switch_frequency_metrics(days: int = 30) -> Dict[str, Any]:
    """Calculate switch frequency metrics"""
    try:
        switches = await get_switches(1000)
        
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(days=days)
        
        # Filter switches
        filtered_switches = []
        for switch in switches:
            try:
                timestamp = parse_timestamp(switch["timestamp"])
                if timestamp >= cutoff_time:
                    filtered_switches.append({
                        **switch,
                        "_parsed_timestamp": timestamp
                    })
            except Exception as e:
                print(f"Error parsing timestamp in switch_frequency: {e}")
                continue
        
        total_switches = len(filtered_switches)
        
        # Calculate for timeframes
        timeframes = {"24h": 0, "48h": 0, "5d": 0, "7d": 0, "30d": total_switches}
        
        for switch in filtered_switches:
            try:
                timestamp = switch["_parsed_timestamp"]
                time_ago = (now - timestamp).total_seconds()
                
                if time_ago <= 24 * 3600:
                    timeframes["24h"] += 1
                if time_ago <= 48 * 3600:
                    timeframes["48h"] += 1
                if time_ago <= 5 * 24 * 3600:
                    timeframes["5d"] += 1
                if time_ago <= 7 * 24 * 3600:
                    timeframes["7d"] += 1
            except Exception as e:
                print(f"Error calculating timeframes: {e}")
                continue
        
        avg_switches_per_day = total_switches / days if days > 0 else 0
        
        return {
            "total_switches": total_switches,
            "avg_switches_per_day": avg_switches_per_day,
            "timeframes": timeframes
        }
        
    except Exception as e:
        print(f"Error in get_switch_frequency_metrics: {e}")
        print(traceback.format_exc())
        return {
            "total_switches": 0,
            "avg_switches_per_day": 0,
            "timeframes": {"24h": 0, "48h": 0, "5d": 0, "7d": 0, "30d": 0}
        }