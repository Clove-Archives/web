"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
WebSocket connection manager
Handles real-time connections and broadcasts
"""

import json
import asyncio
import weakref
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "all": set(),
            "authenticated": set()
        }
        self._weak_connections = weakref.WeakSet()
        self._connection_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, group: str = "all"):
        """Connect a WebSocket client to a group"""
        await websocket.accept()
        
        async with self._connection_lock:
            self.active_connections[group].add(websocket)
            self._weak_connections.add(websocket)
            
        print(f"Client connected to group: {group}. Total: {len(self.active_connections[group])}")

    def disconnect(self, websocket: WebSocket, group: str = "all"):
        """Disconnect a WebSocket client from all groups"""
        for group_name, group_set in self.active_connections.items():
            group_set.discard(websocket)
            
        print(f"Client disconnected. Remaining in 'all': {len(self.active_connections['all'])}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str, group: str = "all"):
        """Broadcast message to all connections in a group"""
        if group not in self.active_connections:
            print(f"Warning: Group '{group}' not found")
            return
            
        disconnected = set()
        connections = list(self.active_connections[group])
        
        print(f"Broadcasting to {len(connections)} clients in group '{group}'")
        
        for connection in connections:
            try:
                await connection.send_text(message)
            except (WebSocketDisconnect, RuntimeError) as e:
                print(f"Client disconnected during broadcast: {e}")
                disconnected.add(connection)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, group)
        
        print(f"Broadcast complete. Removed {len(disconnected)} dead connections")

    async def broadcast_json(self, data: dict, group: str = "all"):
        """Broadcast JSON data to all connections in a group"""
        message = json.dumps(data)
        await self.broadcast(message, group)

# Global connection manager instance
manager = ConnectionManager()

# Helper functions for broadcasting updates
async def broadcast_fronting_update(fronters_data: dict):
    """Broadcast a fronting update to all connected clients"""
    await manager.broadcast_json({
        "type": "fronters_update",
        "data": fronters_data
    })

async def broadcast_mental_state_update(state_data: dict):
    """Broadcast a mental state update to all connected clients"""
    await manager.broadcast_json({
        "type": "mental_state_update",
        "data": state_data
    })

async def broadcast_frontend_update(update_type: str, data: dict):
    """Broadcast a generic frontend update"""
    await manager.broadcast_json({
        "type": update_type,
        "data": data
    })