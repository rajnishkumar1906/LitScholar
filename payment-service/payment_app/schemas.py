# payment_app/schemas.py
from pydantic import BaseModel
from typing import Optional

class CheckoutSessionRequest(BaseModel):
    user_id: int
    email: str
    plan_id: str

class SubscriptionStatus(BaseModel):
    user_id: int
    is_active: bool
    plan_name: Optional[str] = None
    expires_at: Optional[float] = None

class MockPaymentRequest(BaseModel):
    user_id: int
    email: str
    plan_id: str

class CancelSubscriptionRequest(BaseModel):
    user_id: int