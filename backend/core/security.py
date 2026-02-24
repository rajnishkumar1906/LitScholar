from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError # type: ignore
from core.config import settings
from core.db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

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
    
def get_current_user(token: str = Depends(oauth2_scheme)):
    print(f"[JWT DEBUG] Token received (first 30 chars): {token[:30]}...")
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        print("[JWT DEBUG] Full decoded payload:", payload)
        
        sub = payload.get("sub")
        if sub is None:
            print("[JWT DEBUG] No 'sub' key found in token!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject (sub) claim",
            )
        
        print(f"[JWT DEBUG] Valid user: {sub}")
        return sub
    except JWTError as e:
        print("[JWT DEBUG] JWT validation failed:", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
        
def require_role(role: str):
    def checker(user=Depends(get_current_user), db=Depends(get_db)):
        with db.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE email=%s", (user,))
            row = cur.fetchone()
            if not row or row[0] != role:
                raise HTTPException(status_code=403)
        return user
    return checker