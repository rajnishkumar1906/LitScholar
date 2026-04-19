from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from auth.schemas import (
    LoginRequest, RegisterRequest , TokenResponse,
    VerifyTokenRequest, VerifyTokenResponse, ForgotPasswordRequest, ResetPasswordRequest,
    VerifyOtpRequest
)
from core.security import (
    create_access_token, create_refresh_token, get_async_db, 
    set_auth_cookies
)
from core.config import settings
from core.email import email_service
from auth.oauth import oauth
import bcrypt
from datetime import datetime, timedelta
import asyncpg
from jose import jwt, JWTError
import secrets

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest, 
    background_tasks: BackgroundTasks,
    db: asyncpg.Connection = Depends(get_async_db)
):
    print(f"[LOGIN DEBUG] Attempting login for email: {data.email}")
    row = await db.fetchrow(
        "SELECT id, password_hash FROM users WHERE email=$1",
        data.email,
    )

    if not row:
        print(f"[LOGIN DEBUG] User not found: {data.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = row["id"]
    password_hash = row["password_hash"]
    print(f"[LOGIN DEBUG] User found (ID: {user_id}). Verifying password...")

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
        print(f"[LOGIN DEBUG] Invalid password for user: {data.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    print(f"[LOGIN DEBUG] Password verified! Creating tokens for {data.email}")

    # Create JWT tokens
    access_token = create_access_token({"sub": data.email})
    refresh_token = create_refresh_token({"sub": data.email})
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Delete existing refresh token for this user
    try:
        await db.execute(
            "DELETE FROM refresh_tokens WHERE user_id = $1",
            user_id
        )

        # Insert new refresh token
        await db.execute(
            """
            INSERT INTO refresh_tokens (token, user_id, expires_at, created_at, updated_at)
            VALUES ($1, $2, $3, NOW(), NOW())
            """,
            refresh_token, user_id, expires_at,
        )
    except Exception as e:
        print(f"!!! DATABASE ERROR IN LOGIN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error during token storage: {str(e)}")

    # 🚀 LOGIN EMAIL
    async def trigger_login_email(email: str):
        try:
            await email_service.trigger_login_email(email)
            print(f"📧 Login email triggered for {email}")
        except Exception as e:
            print(f"❌ Failed to trigger login email: {e}")

    background_tasks.add_task(trigger_login_email, data.email)

    # Return tokens in response body AND set cookies
    response = JSONResponse(content={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })
    set_auth_cookies(response, access_token, refresh_token)
    return response


@router.post("/register", response_model=TokenResponse)
async def register(
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
    try:
        user_id = await db.fetchval(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
            data.email, hashed,
        )
    except Exception as e:
        print(f"!!! DATABASE ERROR IN REGISTER: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error during user creation: {str(e)}")

    # 🚀 REGISTRATION EMAIL
    async def trigger_welcome_email(email: str):
        try:
            await email_service.trigger_welcome_email(email)
            print(f"📧 Welcome email triggered for {email}")
        except Exception as e:
            print(f"❌ Error calling email service: {e}")

    background_tasks.add_task(trigger_welcome_email, data.email)

    # Create tokens
    access_token = create_access_token({"sub": data.email})
    refresh_token = create_refresh_token({"sub": data.email})
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Insert refresh token
    try:
        await db.execute(
            """
            INSERT INTO refresh_tokens (token, user_id, expires_at, created_at, updated_at)
            VALUES ($1, $2, $3, NOW(), NOW())
            """,
            refresh_token, user_id, expires_at,
        )
    except Exception as e:
        print(f"!!! DATABASE ERROR IN REGISTER TOKEN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error during token storage: {str(e)}")

    # Return tokens in response body AND set cookies
    response = JSONResponse(content={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })
    set_auth_cookies(response, access_token, refresh_token)
    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Refresh access token using refresh token from cookie
    """
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")
    
    # Verify refresh token and get user
    row = await db.fetchrow(
        """
        SELECT u.email, u.id
        FROM refresh_tokens r
        JOIN users u ON r.user_id = u.id
        WHERE r.token = $1 AND r.expires_at > NOW()
        """,
        refresh_token,
    )

    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    email = row["email"]
    user_id = row["id"]
    
    # Create new access token
    new_access_token = create_access_token({"sub": email})
    
    # Create new refresh token (rotation)
    new_refresh_token = create_refresh_token({"sub": email})
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    # Update refresh token in database
    await db.execute(
        """
        UPDATE refresh_tokens 
        SET token = $1, expires_at = $2, updated_at = NOW()
        WHERE user_id = $3
        """,
        new_refresh_token, expires_at, user_id
    )

    response = JSONResponse(content={
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    })
    set_auth_cookies(response, new_access_token, new_refresh_token)
    return response

@router.post("/verify", response_model=VerifyTokenResponse)
async def verify_token(data: VerifyTokenRequest, db: asyncpg.Connection = Depends(get_async_db)):
    """
    Endpoint for other microservices to verify a JWT token and get user data.
    """
    try:
        payload = jwt.decode(
            data.token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        # Get user details from DB
        user = await db.fetchrow(
            "SELECT id, email, full_name FROM users WHERE email = $1",
            email
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return VerifyTokenResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            is_active=True
        )
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/logout")
async def logout(
    request: Request,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Logout by invalidating refresh token from cookie
    """
    refresh_token = request.cookies.get("refresh_token")
    
    if refresh_token:
        # Delete refresh token from database
        await db.execute(
            "DELETE FROM refresh_tokens WHERE token = $1",
            refresh_token
        )
    
    response = JSONResponse(content={"success": True, "message": "Logged out successfully"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Generate a password reset token and send an email
    """
    # 1. Check if user exists
    user = await db.fetchrow("SELECT id, email FROM users WHERE email = $1", data.email)
    if not user:
        # For security, don't reveal if user exists. Just return success message.
        return {"message": "If your email is registered, you will receive a reset link shortly."}

    # 2. Generate secure 6-digit OTP
    otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # 3. Store OTP in database
    try:
        await db.execute(
            """
            INSERT INTO password_reset_tokens (user_id, otp, expires_at)
            VALUES ($1, $2, $3)
            """,
            user["id"], otp, expires_at
        )
    except Exception as e:
        print(f"❌ Error storing OTP: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    # 4. Trigger email via email-service
    async def trigger_reset_email(email: str, username: str, otp: str):
        try:
            await email_service.trigger_password_reset_email(email, username, otp)
            print(f"📧 Password reset email triggered for {email}")
        except Exception as e:
            print(f"⚠️ Error sending password reset email: {e}")

    background_tasks.add_task(trigger_reset_email, user["email"], user["email"].split('@')[0], otp)

    return {"message": "If your email is registered, you will receive a reset link shortly."}

@router.post("/verify-otp")
async def verify_otp(
    data: VerifyOtpRequest,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Verify if the OTP is valid for the given email
    """
    print(f"DEBUG: Verifying OTP for email: {data.email}, OTP: {data.otp}")
    
    user = await db.fetchrow("SELECT id FROM users WHERE email = $1", data.email)
    if not user:
        print(f"DEBUG: User not found for email: {data.email}")
        raise HTTPException(status_code=400, detail="Invalid request")

    print(f"DEBUG: Found user ID: {user['id']}")

    reset_record = await db.fetchrow(
        """
        SELECT id, expires_at, used, otp
        FROM password_reset_tokens 
        WHERE user_id = $1 AND otp = $2
        ORDER BY created_at DESC LIMIT 1
        """,
        user["id"], data.otp
    )

    if not reset_record:
        # Check if any OTP exists for this user to see if it's just a mismatch
        any_otp = await db.fetchrow("SELECT otp FROM password_reset_tokens WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1", user["id"])
        print(f"DEBUG: OTP mismatch. Sent: '{data.otp}', Expected: '{any_otp['otp'] if any_otp else 'None'}'")
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    print(f"DEBUG: Found reset record. Used: {reset_record['used']}, Expires: {reset_record['expires_at']}")

    if reset_record["used"]:
        print("DEBUG: OTP already used")
        raise HTTPException(status_code=400, detail="This OTP has already been used")

    if reset_record["expires_at"].replace(tzinfo=None) < datetime.utcnow():
        print(f"DEBUG: OTP expired at {reset_record['expires_at']}")
        raise HTTPException(status_code=400, detail="This OTP has expired")

    print("DEBUG: OTP verification successful")
    return {"message": "OTP verified successfully"}


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Verify the OTP and update the password
    """
    # 1. Find user by email
    user = await db.fetchrow("SELECT id, password_hash FROM users WHERE email = $1", data.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")

    if user["password_hash"] == "GOOGLE_OAUTH":
        raise HTTPException(
            status_code=400,
            detail="This account uses Google login. Password cannot be reset.",
        )

    # 2. Find latest valid OTP for this user
    reset_record = await db.fetchrow(
        """
        SELECT id, expires_at, used 
        FROM password_reset_tokens 
        WHERE user_id = $1 AND otp = $2
        ORDER BY created_at DESC LIMIT 1
        """,
        user["id"], data.otp
    )

    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    if reset_record["used"]:
        raise HTTPException(status_code=400, detail="This OTP has already been used")

    if reset_record["expires_at"].replace(tzinfo=None) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This OTP has expired")

    # 3. Hash new password
    import anyio
    password_hash = await anyio.to_thread.run_sync(
        bcrypt.hashpw, data.new_password.encode(), bcrypt.gensalt()
    )
    password_hash_str = password_hash.decode()

    # 4. Update user password and mark token as used
    try:
        print(f"DEBUG: Updating password for user ID: {user['id']}")
        # Update user password
        await db.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            password_hash_str, user["id"]
        )
        
        # Mark all OTPs for this user as used
        await db.execute(
            "UPDATE password_reset_tokens SET used = TRUE WHERE user_id = $1",
            user["id"]
        )
        print(f"✅ Password updated successfully in DB for user {data.email}")

    except Exception as e:
        print(f"❌ Error updating password: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password")

    return {"message": "Password reset successfully. You can now log in with your new password."}


@router.post("/verify", response_model=VerifyTokenResponse)
async def verify_token(
    request: VerifyTokenRequest,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Internal endpoint for other services to verify JWT tokens
    """
    try:
        # Decode token
        payload = jwt.decode(
            request.token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        user = await db.fetchrow(
            "SELECT id, email, full_name FROM users WHERE email = $1",
            email
        )
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return VerifyTokenResponse(
            id=user["id"],
            email=user["email"],
            full_name=user.get("full_name"),
            is_active=True
        )
        
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")


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
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Google OAuth callback - returns tokens in URL fragment
    """
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
        refresh_token = create_refresh_token({"sub": email})
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Delete existing refresh token for this user
        await db.execute(
            "DELETE FROM refresh_tokens WHERE user_id = $1",
            user_id
        )

        # Insert new refresh token
        await db.execute(
            """
            INSERT INTO refresh_tokens (token, user_id, expires_at, created_at, updated_at)
            VALUES ($1, $2, $3, NOW(), NOW())
            """,
            refresh_token, user_id, expires_at,
        )

        # Set httpOnly cookies; redirect without tokens in URL (cookie-first auth)
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        redirect_url = f"{frontend_url}/auth?oauth=success"
        response = RedirectResponse(url=redirect_url, status_code=302)
        set_auth_cookies(response, access_token, refresh_token)
        return response

    except Exception as e:
        error_url = f"{settings.FRONTEND_URL}/?error=google_auth_failed"
        return RedirectResponse(url=error_url)