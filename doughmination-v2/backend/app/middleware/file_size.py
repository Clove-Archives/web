"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
File size limit middleware
Prevents uploads larger than configured maximum
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import MAX_AVATAR_SIZE

class FileSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit file upload sizes
    Checks Content-Length header before processing the request
    """
    
    async def dispatch(self, request: Request, call_next):
        # Only check POST requests to avatar endpoints
        if request.method == 'POST' and '/avatar' in request.url.path:
            try:
                content_length = request.headers.get('content-length')
                
                if content_length and int(content_length) > MAX_AVATAR_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"File size exceeds the limit of {MAX_AVATAR_SIZE // (1024 * 1024)}MB"
                        }
                    )
            except (ValueError, TypeError):
                # If we can't parse content-length, let it through
                # The actual upload handler will catch oversized files
                pass
        
        # Continue processing the request
        response = await call_next(request)
        return response