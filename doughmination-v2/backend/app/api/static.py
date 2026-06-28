"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Static file serving and dynamic embeds
Handles frontend, WebSocket, avatars, SEO embeds
"""

import json
import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import FileResponse, Response, HTMLResponse

from app.core.config import STATIC_DIR, DATA_DIR, BASE_URL
from app.core.websocket import manager
from app.services.pluralkit import get_members
from app.utils.html import escape_html, normalize_hex

router = APIRouter()

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with improved error handling"""
    
    # Accept connection
    await manager.connect(websocket, "all")
    
    # Send connection confirmation
    try:
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "WebSocket connected successfully"
        })
        print(f"WebSocket client connected from {websocket.client}")
    except Exception as e:
        print(f"Error sending connection confirmation: {e}")
        manager.disconnect(websocket, "all")
        return
    
    try:
        while True:
            try:
                # Wait for messages with timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0
                )
                
                # Handle message types
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "subscribe":
                    await websocket.send_json({
                        "type": "subscribed",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_json({
                        "type": "keepalive",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                except Exception:
                    break
                    
            except WebSocketDisconnect:
                break
                
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
                
    except WebSocketDisconnect:
        print("WebSocket disconnected normally")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket, "all")
        print("WebSocket connection closed")

# ============================================================================
# SEO & CRAWLER FILES
# ============================================================================

@router.get("/robots.txt")
async def robots_txt():
    """Serve enhanced robots.txt"""
    robots_content = """# Doughmination System® - Robots.txt
User-agent: *
Allow: /
Crawl-delay: 1

# Allow specific bots
User-agent: Googlebot
Allow: /
Crawl-delay: 0

User-agent: Bingbot
Allow: /
Crawl-delay: 1

User-agent: Slurp
Allow: /

# Block bad bots
User-agent: AhrefsBot
Disallow: /

User-agent: SemrushBot
Disallow: /

User-agent: MJ12bot
Disallow: /

# Block common exploit attempts
Disallow: /vendor/
Disallow: /.env
Disallow: /HNAP1/
Disallow: /onvif/
Disallow: /PSIA/
Disallow: /index.php
Disallow: /eval-stdin.php
Disallow: /api/
Disallow: /admin/
Disallow: /ws

# Sitemap
Sitemap: https://doughmination.co.uk/sitemap.xml
"""
    return Response(content=robots_content, media_type="text/plain")

@router.get("/sitemap.xml")
async def sitemap_xml():
    """Generate dynamic sitemap with all member pages"""
    try:
        members = await get_members()
        
        sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <!-- Homepage -->
  <url>
    <loc>https://doughmination.co.uk/</loc>
    <lastmod>{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  
  <!-- Admin/Login Pages -->
  <url>
    <loc>https://doughmination.co.uk/admin/login</loc>
    <lastmod>{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
"""
        
        # Add member pages
        for member in members:
            member_name = member.get('name', '').replace(' ', '%20')
            avatar_url = member.get('avatar_url', '')
            display_name = member.get('display_name') or member.get('name')
            
            sitemap += f"""  <!-- Member: {display_name} -->
  <url>
    <loc>https://doughmination.co.uk/{member_name}</loc>
    <lastmod>{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>"""
            
            if avatar_url:
                sitemap += f"""
    <image:image>
      <image:loc>{avatar_url}</image:loc>
      <image:title>{display_name}</image:title>
    </image:image>"""
            
            sitemap += """
  </url>
"""
        
        sitemap += "</urlset>"
        return Response(content=sitemap, media_type="application/xml")
        
    except Exception as e:
        print(f"Error generating sitemap: {e}")
        return Response(
            content=f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://doughmination.co.uk/</loc>
    <lastmod>{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</lastmod>
  </url>
</urlset>""",
            media_type="application/xml"
        )

@router.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    raise HTTPException(status_code=404, detail="Favicon not found")

# ============================================================================
# AVATAR SERVING
# ============================================================================

@router.get("/avatars/{filename}")
async def get_avatar(filename: str):
    """Serve avatar images with proper content type"""
    # Sanitize filename
    safe_filename = Path(filename).name
    file_path = DATA_DIR / safe_filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    # Determine media type
    media_type = "application/octet-stream"
    if safe_filename.lower().endswith(('.jpg', '.jpeg')):
        media_type = "image/jpeg"
    elif safe_filename.lower().endswith('.png'):
        media_type = "image/png"
    elif safe_filename.lower().endswith('.gif'):
        media_type = "image/gif"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )

# ============================================================================
# DYNAMIC EMBEDS FOR MEMBER PAGES
# ============================================================================

@router.get("/fronting")
async def serve_fronting_page(request: Request):
    """Serve fronting page with dynamic meta tags"""
    try:
        from app.services.pluralkit import get_fronters
        
        fronters_data = await get_fronters()
        members = fronters_data.get("members", [])
        
        if not members:
            return FileResponse(STATIC_DIR / "index.html")
        
        # Build fronter names
        fronter_names = []
        for member in members:
            name = escape_html(member.get("display_name") or member.get("name", "Unknown"))
            fronter_names.append(name)
        
        # Primary fronter
        primary = members[0]
        primary_name = escape_html(primary.get("display_name") or primary.get("name", "Unknown"))
        primary_pronouns = escape_html(primary.get("pronouns") or "they/them")
        primary_color = normalize_hex(primary.get("color"))
        primary_avatar = primary.get("avatar_url") or "https://c.stupid.cat/assets/favicon/avatar.png"
        primary_description = escape_html(
            primary.get("description") or "Currently fronting in the Doughmination System®"
        )
        
        # Create title and description
        if len(fronter_names) == 1:
            title = f"{primary_name} is Fronting"
            description = f"{primary_name} ({primary_pronouns}) is currently fronting in the Doughmination System®"
        else:
            fronters_list = ", ".join(fronter_names[:-1]) + f" and {fronter_names[-1]}"
            title = f"{fronters_list} are Fronting"
            description = f"{fronters_list} are currently co-fronting in the Doughmination System®"
        
        keywords = f"plural system, fronting, current fronters, Doughmination System, {', '.join(fronter_names)}"
        
        # Structured data
        members_structured = []
        for member in members:
            member_name = escape_html(member.get("display_name") or member.get("name", "Unknown"))
            member_avatar = member.get("avatar_url") or "https://c.stupid.cat/assets/favicon/avatar.png"
            member_url_name = member.get("name", "").replace(" ", "%20")
            
            members_structured.append({
                "@type": "Person",
                "name": member_name,
                "image": member_avatar,
                "url": f"https://doughmination.co.uk/{member_url_name}",
                "identifier": member.get("id", "")
            })
        
        structured_data = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "ItemList",
      "name": "Current Fronters",
      "description": "{description}",
      "itemListElement": {json.dumps(members_structured)}
    }}
    </script>"""
        
        # Read and modify index.html
        with open(STATIC_DIR / "index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        meta_head = f"""
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <title>{title} | Doughmination System®</title>
    <meta name="description" content="{description}" />
    <meta name="keywords" content="{keywords}" />
    <meta name="theme-color" content="{primary_color}" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:image" content="{primary_avatar}" />
    <meta property="og:url" content="https://doughmination.co.uk/fronting" />
    {structured_data}
</head>
"""
        
        html_content = re.sub(r"<head>.*?</head>", meta_head, html_content, flags=re.DOTALL)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"Error serving fronting page: {e}")
        return FileResponse(STATIC_DIR / "index.html")

@router.get("/{member_name}")
async def serve_member_page(member_name: str, request: Request):
    """Serve member page with dynamic meta tags"""
    
    # Skip non-member routes
    skip_routes = ['api', 'admin', 'assets', 'avatars', 'favicon.ico', 
                   'robots.txt', 'sitemap.xml', 'ws', 'fonts']
    if any(member_name.startswith(route) for route in skip_routes):
        raise HTTPException(status_code=404)
    
    try:
        members = await get_members()
        member = None
        
        for m in members:
            if m.get("name", "").lower() == member_name.lower():
                member = m
                break
        
        if not member:
            return FileResponse(STATIC_DIR / "index.html")

        # Extract member data
        color = normalize_hex(member.get("color"))
        pronouns = escape_html(member.get("pronouns") or "they/them")
        display_name = escape_html(member.get("display_name") or member.get("name"))
        description = escape_html(
            member.get("description") or f"Member of the Doughmination System®"
        )
        avatar_url = member.get("avatar_url") or "https://c.stupid.cat/assets/favicon/avatar.png"
        member_id = member.get("id", "")
        
        # Build keywords
        tags = member.get("tags", [])
        tags_text = ", ".join(tags) if tags else ""
        keywords = f"plural system, {display_name}, system member, Doughmination System, {pronouns}"
        if tags_text:
            keywords += f", {tags_text}"
        
        # Structured data
        structured_data = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Person",
      "name": "{display_name}",
      "description": "{description}",
      "image": "{avatar_url}",
      "url": "https://doughmination.co.uk/{member_name}",
      "identifier": "{member_id}"
    }}
    </script>"""
        
        # Read and modify index.html
        with open(STATIC_DIR / "index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        meta_head = f"""
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <title>{display_name} ({pronouns}) | Doughmination System®</title>
    <meta name="description" content="{description} - Member of the Doughmination System®. Pronouns: {pronouns}" />
    <meta name="keywords" content="{keywords}" />
    <meta name="theme-color" content="{color}" />
    <meta property="og:title" content="{display_name} - {pronouns}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:image" content="{avatar_url}" />
    <meta property="og:url" content="https://doughmination.co.uk/{member_name}" />
    {structured_data}
</head>
"""
        
        html_content = re.sub(r"<head>.*?</head>", meta_head, html_content, flags=re.DOTALL)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"Error serving member page: {e}")
        return FileResponse(STATIC_DIR / "index.html")

# ============================================================================
# ROOT / FRONTEND
# ============================================================================

@router.get("/")
async def serve_root():
    """Serve the main frontend application"""
    return FileResponse(STATIC_DIR / "index.html")