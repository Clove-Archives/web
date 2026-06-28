"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Authentication API endpoints
Handles login, signup, and user info
"""

from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models import UserResponse, UserCreate, LoginRequest
from app.services.user_service import verify_user, get_user_by_username, create_user, get_users
from app.core.security import create_access_token, verify_turnstile_token
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/api/login")
async def login(request: Request):
    """
    Unified login endpoint that handles both JSON (with Turnstile) and form data (legacy)
    """
    content_type = request.headers.get("content-type", "")
    
    # Handle JSON requests (new frontend with Turnstile)
    if "application/json" in content_type:
        try:
            body = await request.json()
            login_data = LoginRequest(**body)
            
            # Get client IP for Turnstile verification
            client_ip = request.client.host if request.client else None
            
            # Verify Turnstile token
            is_valid = await verify_turnstile_token(login_data.turnstile_token, client_ip)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security verification failed"
                )
            
            username = login_data.username
            password = login_data.password
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request format"
            )
    
    # Handle form data requests (legacy compatibility)
    else:
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
            
            if not username or not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username and password required"
                )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request format"
            )
    
    # Authenticate user
    user = verify_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token
    token = create_access_token({
        "sub": user.username,
        "id": user.id,
        "display_name": user.display_name,
        "admin": user.is_admin,
        "owner": user.is_owner,
        "pet": user.is_pet,
        "avatar_url": getattr(user, 'avatar_url', None)
    })

    return {"access_token": token, "token_type": "bearer", "success": True}

@router.post("/api/signup")
async def signup(request: Request):
    """
    Public endpoint for user signup with Turnstile verification
    Creates a new user account without admin privileges
    """
    try:
        body = await request.json()
        
        # Extract and validate required fields
        username = body.get("username", "").strip()
        password = body.get("password", "")
        display_name = body.get("display_name", "").strip() or None
        turnstile_token = body.get("turnstile_token", "")
        
        # Validate required fields
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is required"
            )
        
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )
        
        if len(password) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 10 characters long"
            )
        
        if not turnstile_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security verification is required"
            )
        
        # Verify Turnstile token
        client_ip = request.client.host if request.client else None
        is_valid = await verify_turnstile_token(turnstile_token, client_ip)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security verification failed"
            )
        
        # Check if username already exists (case-insensitive)
        users = get_users()
        username_lower = username.lower()
        if any(user.username.lower() == username_lower for user in users):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Create the user (explicitly set is_admin=False for signup users)
        user_create = UserCreate(
            username=username,
            password=password,
            display_name=display_name,
            is_admin=False,  # Signup users never get admin privileges
            is_pet=False     # Signup users never get pet privileges
        )
        
        new_user = create_user(user_create, requesting_user=None)
        
        return {
            "success": True,
            "message": "Account created successfully",
            "user": UserResponse(
                id=new_user.id,
                username=new_user.username,
                display_name=new_user.display_name,
                is_admin=new_user.is_admin,
                is_owner=new_user.is_owner,
                is_pet=new_user.is_pet,
                avatar_url=getattr(new_user, 'avatar_url', None)
            )
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )

@router.get("/api/users/check-username")
async def check_username_availability(username: str):
    """
    Public endpoint to check if a username is available (case-insensitive)
    Used during signup to provide real-time feedback
    """
    if not username or not username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username parameter is required"
        )
    
    users = get_users()
    username_lower = username.strip().lower()
    
    # Check if username exists (case-insensitive)
    exists = any(user.username.lower() == username_lower for user in users)
    
    return {"username": username, "exists": exists, "available": not exists}

@router.get("/api/user_info", response_model=UserResponse)
def get_user_info(user=Depends(get_current_user)):
    """Get current authenticated user's information"""
    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        is_admin=user.is_admin,
        is_owner=user.is_owner,
        is_pet=user.is_pet,
        avatar_url=getattr(user, 'avatar_url', None)
    )

@router.get("/api/auth/is_admin")
async def check_admin(user=Depends(get_current_user)):
    """Check if current user is admin"""
    return {"isAdmin": user.is_admin}

@router.get("/api/auth/is_pet")
async def check_pet(user=Depends(get_current_user)):
    """Check if current user is pet"""
    return {"isPet": user.is_pet}

@router.get("/api/auth/is_owner")
async def check_owner(user=Depends(get_current_user)):
    """Check if current user is owner"""
    return {"isOwner": user.is_owner}