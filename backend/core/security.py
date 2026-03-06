from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from core.config import settings
from core.db import get_async_db
import asyncpg

# Keep this for Swagger UI and backward compatibility
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme)
):
    # Try to get token from cookie first
    access_token = request.cookies.get("access_token")
    
    # If no cookie, try Authorization header (for Swagger/API clients)
    if not access_token and token:
        # Handle case where token might be a Bearer token object
        if hasattr(token, 'credentials'):
            access_token = token.credentials
        else:
            access_token = token
    
    if not access_token:
        print("[JWT DEBUG] No token found in cookie or header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # Remove 'Bearer ' prefix if present
    if access_token.startswith("Bearer "):
        access_token = access_token[7:]
    
    print(f"[JWT DEBUG] Token received (first 30 chars): {access_token[:30]}...")
    
    try:
        payload = jwt.decode(
            access_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        print("[JWT DEBUG] Full decoded payload:", payload)
        
        email = payload.get("sub")
        if email is None:
            print("[JWT DEBUG] No 'sub' key found in token!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject (sub) claim",
            )
        
        print(f"[JWT DEBUG] Valid user: {email}")
        return email  # Return email string for now
        
    except JWTError as e:
        print("[JWT DEBUG] JWT validation failed:", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

async def get_current_user_with_db(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: asyncpg.Connection = Depends(get_async_db),
):
    email = await get_current_user(request, token)
    
    # Get full user from database
    query = "SELECT id, email, full_name FROM users WHERE email = $1"
    user = await db.fetchrow(query, email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return {
        "id": int(user["id"]),
        "email": user["email"],
        "full_name": user["full_name"]
    }

def require_role(role: str):
    async def checker(
        request: Request,
        token: str = Depends(oauth2_scheme),
        db: asyncpg.Connection = Depends(get_async_db)
    ):
        user = await get_current_user_with_db(request, token, db)
        
        # Check user role logic here
        # query = "SELECT role FROM users WHERE id = $1"
        # user_role = await db.fetchval(query, user["id"])
        # if user_role != role:
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        return user
    return checker