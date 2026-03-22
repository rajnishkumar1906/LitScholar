from pydantic import BaseModel, EmailStr
from typing import List, Optional

class EmailSchema(BaseModel):
    email: List[EmailStr]
    subject: str
    body: str

class WelcomeEmailRequest(BaseModel):
    email: EmailStr
    username: Optional[str] = None

class PaymentEmailRequest(BaseModel):
    email : EmailStr
    username : str
    plan_name : str
    amount : float
    payment_id : str
    expiry_date : str