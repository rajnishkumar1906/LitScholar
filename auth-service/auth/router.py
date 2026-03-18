from fastapi import APIRouter, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.responses import RedirectResponse
import httpx
from auth.schemas import LoginRequest, RegisterRequest
from core.security import create_access_token, create_refresh_token, get_async_db, set_auth_cookies
from core.config import settings
from auth.oauth import oauth
import bcrypt
import secrets
from datetime import datetime, timedelta
from jose import jwt
import asyncpg

router = APIRouter()

@router.post("/login")
async def login(
    response: Response,
    data: LoginRequest, 
    db: asyncpg.Connection = Depends(get_async_db)
):
    row = await db.fetchrow(
        "SELECT id, password_hash FROM users WHERE email=$1",
        data.email,
    )

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = row["id"]
    password_hash = row["password_hash"]

    if password_hash == "GOOGLE_OAUTH":
        raise HTTPException(
            status_code=400,
            detail="This account uses Google login",
        )

    # Use to_thread for blocking bcrypt checkpw
    import anyio
    is_valid = await anyio.to_thread.run_sync(
        bcrypt.checkpw, data.password.encode(), password_hash.encode()
    )
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": data.email})
    refresh_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)

    await db.execute(
        """
        INSERT INTO refresh_tokens (token, user_id, expires_at)
        VALUES ($1, $2, $3)
        """,
        refresh_token, user_id, expires_at,
    )

    set_auth_cookies(response, access_token, refresh_token)

    return {"success": True, "message": "Login successful", "email": data.email}

@router.post("/register")
async def register(
    response: Response,
    data: RegisterRequest, 
    background_tasks: BackgroundTasks,
    db: asyncpg.Connection = Depends(get_async_db)
):
    # Check if user exists
    exists = await db.fetchval("SELECT id FROM users WHERE email=$1", data.email)
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password (offload to thread)
    import anyio
    hashed_bytes = await anyio.to_thread.run_sync(
        bcrypt.hashpw, data.password.encode(), bcrypt.gensalt()
    )
    hashed = hashed_bytes.decode()

    # Insert user
    user_id = await db.fetchval(
        "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
        data.email, hashed,
    )

    # Trigger welcome email in background
    async def trigger_welcome_email(email: str):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.EMAIL_SERVICE_URL}/welcome",
                    json={"email": email}
                )
        except Exception as e:
            print(f"❌ Error calling email service: {e}")

    background_tasks.add_task(trigger_welcome_email, data.email)

    # Create tokens
    access_token = create_access_token({"sub": data.email})
    refresh_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Store refresh token
    await db.execute(
        """
        INSERT INTO refresh_tokens (token, user_id, expires_at)
        VALUES ($1, $2, $3)
        """,
        refresh_token, user_id, expires_at,
    )

    set_auth_cookies(response, access_token, refresh_token)

    return {"success": True, "message": "Registration successful", "email": data.email}

@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: asyncpg.Connection = Depends(get_async_db)
):
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    row = await db.fetchrow(
        """
        SELECT u.email
        FROM refresh_tokens r
        JOIN users u ON r.user_id = u.id
        WHERE r.token = $1 AND r.expires_at > NOW()
        """,
        refresh_token,
    )

    if not row:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email = row["email"]
    new_access_token = create_access_token({"sub": email})

    # Note: We keep the existing refresh token in the cookie
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",         
        samesite="lax",       
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {"success": True, "message": "Token refreshed"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"success": True, "message": "Logged out"}

@router.get("/google/login")
async def google_login(request: Request):
    if not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="GOOGLE_REDIRECT_URI not configured")

    try:
        redirect_resp = await oauth.google.authorize_redirect(
            request,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            access_type="offline",
            prompt="consent"
        )
        return redirect_resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth redirect error: {str(e)}")

@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    db: asyncpg.Connection = Depends(get_async_db)
):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        
        if not user_info:
            raise ValueError("No userinfo in token response")

        email = user_info.get("email")
        if not email:
            raise ValueError("Email not provided by Google")

        # Check if user exists
        row = await db.fetchrow("SELECT id FROM users WHERE email=$1", email)

        if row:
            user_id = row["id"]
        else:
            user_id = await db.fetchval(
                """
                INSERT INTO users (email, password_hash)
                VALUES ($1, $2)
                RETURNING id
                """,
                email, "GOOGLE_OAUTH",
            )

        # Create tokens
        access_token = create_access_token({"sub": email})
        refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Store refresh token
        await db.execute(
            """
            INSERT INTO refresh_tokens (token, user_id, expires_at)
            VALUES ($1, $2, $3)
            """,
            refresh_token, user_id, expires_at,
        )

        set_auth_cookies(response, access_token, refresh_token)

        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/dashboard")

    except Exception as e:
        error_url = f"{settings.FRONTEND_URL}/?error=google_auth_failed"
        return RedirectResponse(url=error_url)
