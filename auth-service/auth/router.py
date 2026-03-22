# from fastapi import APIRouter, HTTPException, Depends, Request, Response, BackgroundTasks
# from fastapi.responses import RedirectResponse
# import httpx
# from auth.schemas import LoginRequest, RegisterRequest
# from core.security import create_access_token, create_refresh_token, get_async_db, set_auth_cookies
# from core.config import settings
# from auth.oauth import oauth
# import bcrypt
# import secrets
# from datetime import datetime, timedelta
# from jose import jwt
# import asyncpg

# router = APIRouter()

# @router.post("/login")
# async def login(
#     response: Response,
#     data: LoginRequest, 
#     background_tasks: BackgroundTasks,
#     db: asyncpg.Connection = Depends(get_async_db)
# ):
#     row = await db.fetchrow(
#         "SELECT id, password_hash FROM users WHERE email=$1",
#         data.email,
#     )

#     if not row:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     user_id = row["id"]
#     password_hash = row["password_hash"]

#     if password_hash == "GOOGLE_OAUTH":
#         raise HTTPException(
#             status_code=400,
#             detail="This account uses Google login",
#         )

#     import anyio
#     is_valid = await anyio.to_thread.run_sync(
#         bcrypt.checkpw, data.password.encode(), password_hash.encode()
#     )
#     if not is_valid:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     access_token = create_access_token({"sub": data.email})
#     refresh_token = secrets.token_urlsafe(32)
#     expires_at = datetime.utcnow() + timedelta(days=7)

#     await db.execute(
#         """
#         INSERT INTO refresh_tokens (token, user_id, expires_at)
#         VALUES ($1, $2, $3)
#         """,
#         refresh_token, user_id, expires_at,
#     )

#     set_auth_cookies(response, access_token, refresh_token)

#     # 🚀 LOGIN EMAIL - Using existing /send-email endpoint with FULL HTML body
#     async def trigger_login_email(email: str):
#         try:
#             # Create HTML email content
#             username = email.split('@')[0]
#             current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            
#             html_body = f"""
#                 <html>
#                 <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1a1a1a; background-color: #f9fafb; margin: 0; padding: 0;">
#                     <div style="max-width: 550px; margin: 40px auto; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        
#                         <div style="padding: 30px 40px 10px 40px;">
#                             <h2 style="color: #4F46E5; font-size: 20px; font-weight: 600; margin: 0;">Security Alert: New Login</h2>
#                         </div>
                
#                         <div style="padding: 0 40px 30px 40px;">
#                             <p style="font-size: 15px; margin-top: 20px;">Hi {username},</p>
                            
#                             <p style="font-size: 15px;">A new sign-in was detected for your LitScholar account. If this was you, no further action is required.</p>
                            
#                             <div style="background-color: #f8fafc; border: 1px solid #f1f5f9; border-radius: 6px; padding: 20px; margin: 25px 0;">
#                                 <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
#                                     <tr>
#                                         <td style="color: #64748b; padding-bottom: 8px; width: 80px;">Account</td>
#                                         <td style="font-weight: 500; padding-bottom: 8px;">{email}</td>
#                                     </tr>
#                                     <tr>
#                                         <td style="color: #64748b;">Time</td>
#                                         <td style="font-weight: 500;">{current_time} UTC</td>
#                                     </tr>
#                                 </table>
#                             </div>
                
#                             <p style="font-size: 14px; color: #475569;">
#                                 <strong>Not you?</strong> To protect your account, we recommend changing your password immediately and reviewing your recent activity.
#                             </p>
                            
#                             <div style="margin-top: 30px;">
#                                 <a href="#" style="background-color: #4F46E5; color: #ffffff; padding: 12px 24px; border-radius: 5px; text-decoration: none; font-size: 14px; font-weight: 500; display: inline-block;">Secure Account</a>
#                             </div>
#                         </div>
                
#                         <div style="background-color: #f9fafb; padding: 25px 40px; border-top: 1px solid #e5e7eb; text-align: center;">
#                             <p style="font-size: 13px; color: #94a3b8; margin: 0;">
#                                 Sent by <strong>LitScholar</strong>
#                             </p>
#                             <p style="font-size: 12px; color: #cbd5e1; margin-top: 8px;">
#                                 This is a mandatory security notification. You cannot unsubscribe from security alerts.
#                             </p>
#                         </div>
#                     </div>
#                 </body>
#                 </html>
#                 """
            
#             async with httpx.AsyncClient() as client:
#                 await client.post(
#                     f"{settings.EMAIL_SERVICE_URL}/send-email",
#                     json={
#                         "email": [email],
#                         "subject": "🔐 New Login to LitScholar",
#                         "body": html_body
#                     }
#                 )
#                 print(f"📧 Login email triggered for {email}")
#         except Exception as e:
#             print(f"❌ Failed to trigger login email: {e}")

#     background_tasks.add_task(trigger_login_email, data.email)

#     return {"success": True, "message": "Login successful", "email": data.email}


# @router.post("/register")
# async def register(
#     response: Response,
#     data: RegisterRequest, 
#     background_tasks: BackgroundTasks,
#     db: asyncpg.Connection = Depends(get_async_db)
# ):
#     # Check if user exists
#     exists = await db.fetchval("SELECT id FROM users WHERE email=$1", data.email)
#     if exists:
#         raise HTTPException(status_code=400, detail="Email already registered")

#     # Hash password
#     import anyio
#     hashed_bytes = await anyio.to_thread.run_sync(
#         bcrypt.hashpw, data.password.encode(), bcrypt.gensalt()
#     )
#     hashed = hashed_bytes.decode()

#     # Insert user
#     user_id = await db.fetchval(
#         "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
#         data.email, hashed,
#     )

#     # 🚀 REGISTRATION EMAIL - Using existing /welcome endpoint
#     async def trigger_welcome_email(email: str):
#         try:
#             async with httpx.AsyncClient() as client:
#                 await client.post(
#                     f"{settings.EMAIL_SERVICE_URL}/welcome",
#                     json={
#                         "email": email, 
#                         "username": email.split('@')[0]
#                     }
#                 )
#                 print(f"📧 Welcome email triggered for {email}")
#         except Exception as e:
#             print(f"❌ Error calling email service: {e}")

#     background_tasks.add_task(trigger_welcome_email, data.email)

#     # Create tokens
#     access_token = create_access_token({"sub": data.email})
#     refresh_token = secrets.token_urlsafe(32)
#     expires_at = datetime.utcnow() + timedelta(days=7)

#     # Store refresh token
#     await db.execute(
#         """
#         INSERT INTO refresh_tokens (token, user_id, expires_at)
#         VALUES ($1, $2, $3)
#         """,
#         refresh_token, user_id, expires_at,
#     )

#     set_auth_cookies(response, access_token, refresh_token)

#     return {"success": True, "message": "Registration successful", "email": data.email}


# @router.post("/refresh")
# async def refresh(
#     request: Request,
#     response: Response,
#     db: asyncpg.Connection = Depends(get_async_db)
# ):
#     refresh_token = request.cookies.get("refresh_token")
    
#     if not refresh_token:
#         raise HTTPException(status_code=401, detail="No refresh token")
    
#     row = await db.fetchrow(
#         """
#         SELECT u.email
#         FROM refresh_tokens r
#         JOIN users u ON r.user_id = u.id
#         WHERE r.token = $1 AND r.expires_at > NOW()
#         """,
#         refresh_token,
#     )

#     if not row:
#         raise HTTPException(status_code=401, detail="Invalid refresh token")

#     email = row["email"]
#     new_access_token = create_access_token({"sub": email})

#     response.set_cookie(
#         key="access_token",
#         value=new_access_token,
#         httponly=True,
#         secure=settings.ENVIRONMENT == "production",         
#         samesite="lax",       
#         max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
#         path="/",
#     )

#     return {"success": True, "message": "Token refreshed"}


# @router.post("/logout")
# async def logout(response: Response):
#     response.delete_cookie("access_token", path="/")
#     response.delete_cookie("refresh_token", path="/")
#     return {"success": True, "message": "Logged out"}


# @router.get("/google/login")
# async def google_login(request: Request):
#     if not settings.GOOGLE_REDIRECT_URI:
#         raise HTTPException(status_code=500, detail="GOOGLE_REDIRECT_URI not configured")

#     try:
#         redirect_resp = await oauth.google.authorize_redirect(
#             request,
#             redirect_uri=settings.GOOGLE_REDIRECT_URI,
#             access_type="offline",
#             prompt="consent"
#         )
#         return redirect_resp
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"OAuth redirect error: {str(e)}")


# @router.get("/google/callback")
# async def google_callback(
#     request: Request,
#     response: Response,
#     db: asyncpg.Connection = Depends(get_async_db)
# ):
#     try:
#         token = await oauth.google.authorize_access_token(request)
#         user_info = token.get("userinfo")
        
#         if not user_info:
#             raise ValueError("No userinfo in token response")

#         email = user_info.get("email")
#         if not email:
#             raise ValueError("Email not provided by Google")

#         # Check if user exists
#         row = await db.fetchrow("SELECT id FROM users WHERE email=$1", email)

#         if row:
#             user_id = row["id"]
#         else:
#             user_id = await db.fetchval(
#                 """
#                 INSERT INTO users (email, password_hash)
#                 VALUES ($1, $2)
#                 RETURNING id
#                 """,
#                 email, "GOOGLE_OAUTH",
#             )

#         # Create tokens
#         access_token = create_access_token({"sub": email})
#         refresh_token = secrets.token_urlsafe(32)
#         expires_at = datetime.utcnow() + timedelta(days=7)

#         # Store refresh token
#         await db.execute(
#             """
#             INSERT INTO refresh_tokens (token, user_id, expires_at)
#             VALUES ($1, $2, $3)
#             """,
#             refresh_token, user_id, expires_at,
#         )

#         set_auth_cookies(response, access_token, refresh_token)

#         frontend_url = settings.FRONTEND_URL.rstrip('/')
#         return RedirectResponse(url=f"{frontend_url}/dashboard")

#     except Exception as e:
#         error_url = f"{settings.FRONTEND_URL}/?error=google_auth_failed"
#         return RedirectResponse(url=error_url)


from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
import httpx
from auth.schemas import (
    LoginRequest, RegisterRequest, RefreshRequest, TokenResponse,
    VerifyTokenRequest, VerifyTokenResponse
)
from core.security import create_access_token, create_refresh_token, get_async_db
from core.config import settings
from auth.oauth import oauth
import bcrypt
from datetime import datetime, timedelta
import asyncpg
from jose import jwt, JWTError

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
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

    # Create JWT tokens
    access_token = create_access_token({"sub": data.email})
    refresh_token = create_refresh_token({"sub": data.email})
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

    # 🚀 LOGIN EMAIL
    async def trigger_login_email(email: str):
        try:
            username = email.split('@')[0]
            current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            
            html_body = f"""
                <html>
                <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                    <div style="max-width: 550px; margin: 40px auto; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;">
                        <div style="padding: 30px 40px;">
                            <h2 style="color: #4F46E5;">Security Alert: New Login</h2>
                            <p>Hi {username},</p>
                            <p>A new sign-in was detected for your LitScholar account.</p>
                            <div style="background-color: #f8fafc; padding: 20px; margin: 20px 0;">
                                <p><strong>Account:</strong> {email}</p>
                                <p><strong>Time:</strong> {current_time} UTC</p>
                            </div>
                            <p>If this wasn't you, please secure your account immediately.</p>
                        </div>
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

    # Return tokens in response body
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


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
    user_id = await db.fetchval(
        "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
        data.email, hashed,
    )

    # 🚀 REGISTRATION EMAIL
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
    refresh_token = create_refresh_token({"sub": data.email})
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Insert refresh token
    await db.execute(
        """
        INSERT INTO refresh_tokens (token, user_id, expires_at, created_at, updated_at)
        VALUES ($1, $2, $3, NOW(), NOW())
        """,
        refresh_token, user_id, expires_at,
    )

    # Return tokens in response body
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Refresh access token using refresh token from request body
    """
    refresh_token = request.refresh_token
    
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

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/logout")
async def logout(
    request: RefreshRequest,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Logout by invalidating refresh token
    """
    refresh_token = request.refresh_token
    
    if refresh_token:
        # Delete refresh token from database
        await db.execute(
            "DELETE FROM refresh_tokens WHERE token = $1",
            refresh_token
        )
    
    return {"success": True, "message": "Logged out successfully"}


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

        # Return tokens in URL fragment for frontend to read
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        redirect_url = f"{frontend_url}/auth/callback#access_token={access_token}&refresh_token={refresh_token}"
        
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        error_url = f"{settings.FRONTEND_URL}/?error=google_auth_failed"
        return RedirectResponse(url=error_url)