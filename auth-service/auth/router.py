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
    background_tasks: BackgroundTasks,
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

    # 🚀 LOGIN EMAIL - Using existing /send-email endpoint with FULL HTML body
    async def trigger_login_email(email: str):
        try:
            # Create HTML email content
            username = email.split('@')[0]
            current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 10px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4F46E5;">🔐 New Login Detected</h1>
                    </div>
                    
                    <p>Hello <strong>{username}</strong>,</p>
                    
                    <p>A new login to your LitScholar account was just detected:</p>
                    
                    <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Time:</strong> {current_time} UTC</p>
                        <p style="margin: 5px 0;"><strong>Account:</strong> {email}</p>
                    </div>
                    
                    <p>✅ <strong>If this was you</strong> - You can safely ignore this email.</p>
                    
                    <p>⚠️ <strong>If you didn't login</strong> - Please secure your account immediately:</p>
                    <ul style="margin-bottom: 20px;">
                        <li>Change your password</li>
                        <li>Contact support if you notice any suspicious activity</li>
                    </ul>
                    
                    <hr style="border: none; border-top: 1px solid #eaeaea; margin: 30px 0;">
                    
                    <p style="text-align: center; color: #666;">
                        Happy Reading! 📚<br>
                        <strong>The LitScholar Team</strong>
                    </p>
                    
                    <p style="text-align: center; font-size: 12px; color: #999; margin-top: 30px;">
                        This is an automated message, please do not reply to this email.
                    </p>
                </div>
            </body>
            </html>
            """
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.EMAIL_SERVICE_URL}/send-email",
                    json={
                        "email": [email],
                        "subject": "🔐 New Login to LitScholar",
                        "body": html_body
                    }
                )
                print(f"📧 Login email triggered for {email}")
        except Exception as e:
            print(f"❌ Failed to trigger login email: {e}")

    background_tasks.add_task(trigger_login_email, data.email)

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

    # Hash password
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

    # 🚀 REGISTRATION EMAIL - Using existing /welcome endpoint
    async def trigger_welcome_email(email: str):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.EMAIL_SERVICE_URL}/welcome",
                    json={
                        "email": email, 
                        "username": email.split('@')[0]
                    }
                )
                print(f"📧 Welcome email triggered for {email}")
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