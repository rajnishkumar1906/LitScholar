# from datetime import datetime, timedelta
# from fastapi import Depends, HTTPException, status, Request
# from fastapi.security import OAuth2PasswordBearer
# from jose import jwt, JWTError
# from core.config import settings
# from core.db import get_async_db
# import asyncpg
# import httpx

# # Keep this for Swagger UI and backward compatibility
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(
#         minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
#     )
#     to_encode.update({"exp": expire})
#     return jwt.encode(
#         to_encode,
#         settings.JWT_SECRET,
#         algorithm=settings.JWT_ALGORITHM,
#     )

# def create_refresh_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(
#         days=settings.REFRESH_TOKEN_EXPIRE_DAYS
#     )
#     to_encode.update({"exp": expire})
#     return jwt.encode(
#         to_encode,
#         settings.JWT_SECRET,
#         algorithm=settings.JWT_ALGORITHM,
#     )

# async def get_current_user(
#     request: Request,
#     token: str = Depends(oauth2_scheme)
# ):
#     # Try to get token from cookie first
#     access_token = request.cookies.get("access_token")
    
#     # If no cookie, try Authorization header (for Swagger/API clients)
#     if not access_token and token:
#         access_token = token
    
#     if not access_token:
#         print("[JWT DEBUG] No token found in cookie or header")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated",
#         )
    
#     # Remove 'Bearer ' prefix if present
#     if access_token.startswith("Bearer "):
#         access_token = access_token[7:]
    
#     print(f"[JWT DEBUG] Token received (first 30 chars): {access_token[:30]}...")
    
#     try:
#         payload = jwt.decode(
#             access_token,
#             settings.JWT_SECRET,
#             algorithms=[settings.JWT_ALGORITHM],
#         )
#         print("[JWT DEBUG] Full decoded payload:", payload)
        
#         email = payload.get("sub")
#         if email is None:
#             print("[JWT DEBUG] No 'sub' key found in token!")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Token missing subject (sub) claim",
#             )
        
#         print(f"[JWT DEBUG] Valid user: {email}")
#         return email  # Return email string
        
#     except JWTError as e:
#         print("[JWT DEBUG] JWT validation failed:", str(e))
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#         )

# async def get_current_user_with_db(
#     request: Request,
#     token: str = Depends(oauth2_scheme),
#     db: asyncpg.Connection = Depends(get_async_db),
# ):
#     email = await get_current_user(request, token)
    
#     # Get full user from database
#     query = "SELECT id, email, full_name FROM users WHERE email = $1"
#     user = await db.fetchrow(query, email)
    
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found",
#         )
    
#     return dict(user)

# async def verify_premium_subscription(
#     request: Request,
#     token: str = Depends(oauth2_scheme),
#     db: asyncpg.Connection = Depends(get_async_db)
# ):
#     """
#     Dependency to verify if a user has an active premium subscription.
#     """
#     user = await get_current_user_with_db(request, token, db)
#     user_id = user["id"]
    
#     # RAG service should check the subscriptions table
#     query = "SELECT is_active, plan_name FROM subscriptions WHERE user_id = $1"
#     sub = await db.fetchrow(query, user_id)
    
#     if not sub or not sub["is_active"]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Premium subscription required for this feature"
#         )
    
#     return {**user, "plan": sub["plan_name"]}



from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings
from core.db import get_async_db
import asyncpg
import httpx

security = HTTPBearer(auto_error=False)

async def verify_token_with_auth_service(token: str) -> dict:
    """
    Call auth-service to validate token and get user info
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/verify",
                json={"token": token}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Authentication failed")
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current user by calling auth-service
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    # Verify token with auth service
    user_data = await verify_token_with_auth_service(token)
    return user_data

async def get_current_user_with_db(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: asyncpg.Connection = Depends(get_async_db),
) -> dict:
    """
    Get current user with local database details
    """
    user_data = await get_current_user(credentials)
    
    # Get additional user data from local database if needed
    user_id = user_data.get("id")
    if user_id:
        query = "SELECT id, email, full_name FROM users WHERE id = $1"
        user = await db.fetchrow(query, user_id)
        if user:
            return dict(user)
    
    # Fallback to data from auth-service
    return user_data

async def verify_premium_subscription(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: asyncpg.Connection = Depends(get_async_db)
) -> dict:
    """
    Verify user has active premium subscription
    """
    user_data = await get_current_user(credentials)
    user_id = user_data.get("id")
    
    # Check subscription in local database
    query = "SELECT is_active, plan_name FROM subscriptions WHERE user_id = $1 AND is_active = true"
    sub = await db.fetchrow(query, user_id)
    
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required for this feature"
        )
    
    return {**user_data, "plan": sub["plan_name"]}