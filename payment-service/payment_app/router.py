from fastapi import APIRouter, HTTPException, Depends
from payment_app.schemas import CheckoutSessionRequest, SubscriptionStatus
from payment_app.service import payment_service
from core.db import get_async_db
import asyncpg

router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutSessionRequest):
    """
    Creates a mock checkout session (like Stripe Checkout)
    """
    checkout_url = await payment_service.create_checkout_session(request.user_id, request.email, request.plan_id)
    
    return {
        "checkout_url": checkout_url,
        "message": "Checkout session created successfully"
    }

@router.post("/mock-payment-success")
async def mock_payment_success(
    request: CheckoutSessionRequest,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Simulate a successful payment and update subscription
    """
    await payment_service.update_subscription(request.user_id, request.plan_id, db)
    
    return {
        "success": True,
        "message": f"Successfully subscribed user {request.user_id} to plan {request.plan_id}"
    }

@router.get("/subscription/{user_id}")
async def get_subscription(
    user_id: int,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Check subscription status for a user
    """
    return await payment_service.get_subscription_status(user_id, db)
