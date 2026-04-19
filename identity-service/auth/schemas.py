from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

class VerifyTokenRequest(BaseModel):
    token: str

class VerifyTokenResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool = True

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str