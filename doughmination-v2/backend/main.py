"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

#!/usr/bin/env python3
"""
Doughmination System® Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.file_size import FileSizeLimitMiddleware
from app.core.startup import startup_tasks
from app.api import static, system, members, fronting, auth, users, metrics, admin, member_status, bot, battery
from app.core.config import get_cors_origins
import helper

# Create FastAPI app
app = FastAPI(
    title="Doughmination System API",
    description="Plural system tracker and management API",
    version="2.0.0",
    docs_url=None,
    redoc_url="/docs",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(FileSizeLimitMiddleware)

# Run startup tasks
startup_tasks()

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(members.router, prefix="/api", tags=["Members"])
app.include_router(fronting.router, prefix="/api", tags=["Fronting"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(member_status.router, prefix="/api", tags=["Member Status"])
app.include_router(bot.router, tags=["Bot API"])
app.include_router(battery.router, tags=["Battery"])
app.include_router(helper.router, prefix="/api", tags=["Helper"])  # Visitor logging — must be before static catch-all
app.include_router(static.router, tags=["Static Files"])  # Must be last for catch-all routes

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
