from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from auth.schemas import LoginRequest, RegisterRequest, RefreshRequest, TokenResponse
from core.security import create_access_token
from core.db import get_db
from core.config import settings
from auth.oauth import oauth
from authlib.integrations.starlette_client import OAuth
import bcrypt
import secrets
from datetime import datetime, timedelta


router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db=Depends(get_db)):
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

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

# REGISTER
@router.post("/register")
def register(data: RegisterRequest, db=Depends(get_db)):
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    with db.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM users WHERE email=%s",
            (data.email,),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )

        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (data.email, hashed),
        )
        db.commit()

    return {"status": "user created"}

# REFRESH TOKEN
@router.post("/refresh")
def refresh(data: RefreshRequest, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT u.email
            FROM refresh_tokens r
            JOIN users u ON r.user_id = u.id
            WHERE r.token = %s AND r.expires_at > NOW()
            """,
            (data.refresh_token,),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email = row[0]
    new_access_token = create_access_token({"sub": email})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


@router.get("/google/login")
async def google_login(request: Request):
    print("=== GOOGLE LOGIN START ===")
    print("GOOGLE_CLIENT_ID:", settings.GOOGLE_CLIENT_ID[:10] + "..." if settings.GOOGLE_CLIENT_ID else "MISSING")
    print("GOOGLE_CLIENT_SECRET:", settings.GOOGLE_CLIENT_SECRET[:5] + "..." if settings.GOOGLE_CLIENT_SECRET else "MISSING")
    print("GOOGLE_REDIRECT_URI:", settings.GOOGLE_REDIRECT_URI)

    if not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="GOOGLE_REDIRECT_URI not configured")

    try:
        # Best practice: request offline access + force consent screen
        redirect_resp = await oauth.google.authorize_redirect(
            request,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            access_type="offline",  # Ensures refresh_token is possible (optional but good)
            prompt="consent"        # Forces Google to show consent even if already approved
        )
        print("Redirecting user to Google:", redirect_resp.headers.get("location", "MISSING LOCATION"))
        return redirect_resp
    except Exception as e:
        print("OAuth redirect failed:", str(e))
        raise HTTPException(status_code=500, detail=f"OAuth redirect error: {str(e)}")


# GOOGLE CALLBACK - handle redirect from Google
@router.get("/google/callback")
async def google_callback(request: Request, db=Depends(get_db)):
    print("=== GOOGLE CALLBACK RECEIVED ===")
    print("Query params:", dict(request.query_params))

    try:
        # Exchange code for tokens
        token = await oauth.google.authorize_access_token(request)
        print("[Callback] Tokens received keys:", list(token.keys()))

        # Get user info
        user_info = token.get("userinfo")
        if not user_info:
            raise ValueError("No userinfo in token response")

        email = user_info.get("email")
        print(f"[Callback] User email: {email}")

        if not email:
            raise ValueError("Email not provided by Google")

        # Check if user exists
        with db.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            row = cur.fetchone()

            if row:
                user_id = row[0]
                print(f"[Callback] Existing user found, ID: {user_id}")
            else:
                print("[Callback] New user - creating record")
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

        # Create your app's JWT tokens
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

        # Build frontend redirect URL
        frontend_url = settings.FRONTEND_URL.rstrip('/')  # remove trailing slash if any
        redirect_url = f"{frontend_url}/?access_token={access_token}&refresh_token={refresh_token}"

        print(f"[Callback] Redirecting to frontend: {redirect_url}")
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        print(f"[Callback] ERROR: {str(e)}")
        # Optional: redirect to error page instead of raising
        error_url = f"{settings.FRONTEND_URL}/?error=google_auth_failed&error_description={str(e)}"
        return RedirectResponse(url=error_url)