from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse
from auth.schemas import LoginRequest, RegisterRequest
from core.security import create_access_token, create_refresh_token
from core.db import get_db
from core.config import settings
from auth.oauth import oauth
import bcrypt
import secrets
from datetime import datetime, timedelta
from jose import jwt

router = APIRouter()

@router.post("/login")
async def login(
    response: Response,
    data: LoginRequest, 
    db=Depends(get_db)
):
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, password_hash FROM users WHERE email=%s",
            (data.email,),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, password_hash = row

    if password_hash == "GOOGLE_OAUTH":
        raise HTTPException(
            status_code=400,
            detail="This account uses Google login",
        )

    if not bcrypt.checkpw(data.password.encode(), password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": data.email})
    refresh_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)

    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO refresh_tokens (token, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (refresh_token, user_id, expires_at),
        )
        db.commit()

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )

    return {"success": True, "message": "Login successful", "email": data.email}

@router.post("/register")
async def register(
    response: Response,
    data: RegisterRequest, 
    db=Depends(get_db)
):
    # Check if user exists
    with db.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email=%s", (data.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    # Insert user
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
            (data.email, hashed),
        )
        user_id = cur.fetchone()[0]
        db.commit()

    # Create tokens
    access_token = create_access_token({"sub": data.email})
    refresh_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Store refresh token
    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO refresh_tokens (token, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (refresh_token, user_id, expires_at),
        )
        db.commit()

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )

    return {"success": True, "message": "Registration successful", "email": data.email}

@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db=Depends(get_db)
):
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT u.email
            FROM refresh_tokens r
            JOIN users u ON r.user_id = u.id
            WHERE r.token = %s AND r.expires_at > NOW()
            """,
            (refresh_token,),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email = row[0]
    new_access_token = create_access_token({"sub": email})

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
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
    db=Depends(get_db)
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
        with db.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            row = cur.fetchone()

            if row:
                user_id = row[0]
            else:
                cur.execute(
                    """
                    INSERT INTO users (email, password_hash)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (email, "GOOGLE_OAUTH"),
                )
                user_id = cur.fetchone()[0]
                db.commit()

        # Create tokens
        access_token = create_access_token({"sub": email})
        refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Store refresh token
        with db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO refresh_tokens (token, user_id, expires_at)
                VALUES (%s, %s, %s)
                """,
                (refresh_token, user_id, expires_at),
            )
            db.commit()

        # Set cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/",
        )

        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/dashboard")

    except Exception as e:
        error_url = f"{settings.FRONTEND_URL}/?error=google_auth_failed"
        return RedirectResponse(url=error_url)