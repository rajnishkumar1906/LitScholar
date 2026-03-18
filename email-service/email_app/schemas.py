from pydantic import BaseModel, EmailStr
from typing import List, Optional

class EmailSchema(BaseModel):
    email: List[EmailStr]
    subject: str
    body: str

class WelcomeEmailRequest(BaseModel):
    email: EmailStr
    username: Optional[str] = None
