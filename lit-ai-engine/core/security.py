from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings
from core.db import get_async_db
import asyncpg
import httpx

# Switch to HTTPBearer for Authorization header support
security = HTTPBearer(auto_error=False)

def get_token_from_header_or_cookie(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract token from either the Authorization header or the access_token cookie.
    """
    # 1. Try Authorization Header
    if credentials:
        return credentials.credentials
        
    # 2. Try Cookie
    token = request.cookies.get("access_token")
    if token:
        return token
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def verify_token_with_user_service(token: str) -> dict:
    """
    Call user-service to validate token and get user info.
    This allows microservices to remain stateless regarding JWT secrets.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.USER_SERVICE_URL}/auth/verify",
                json={"token": token}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                detail = response.json().get("detail", "Authentication failed")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=detail
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User service unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SECURITY ERROR] Verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get the current user by verifying the token with user-service.
    """
    token = get_token_from_header_or_cookie(request, credentials)
    user_data = await verify_token_with_user_service(token)
    return user_data

async def get_current_user_with_db(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: asyncpg.Connection = Depends(get_async_db),
) -> dict:
    """
    Dependency to get current user with full details from the local database.
    """
    user_data = await get_current_user(request, credentials)
    
    # Get user details from local database
    user_id = user_data.get("id")
    if user_id:
        query = "SELECT id, email, full_name FROM users WHERE id = $1"
        user = await db.fetchrow(query, user_id)
        if user:
            return dict(user)
    
    # Fallback to data from user-service if not in local DB yet
    return user_data
