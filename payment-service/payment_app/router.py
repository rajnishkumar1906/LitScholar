from fastapi import APIRouter, HTTPException, Depends, Request
from payment_app.schemas import CheckoutSessionRequest, SubscriptionStatus, MockPaymentRequest, CancelSubscriptionRequest
from payment_app.service import payment_service
from core.db import get_async_db
from core.config import settings
import razorpay
import asyncpg
import json

router = APIRouter()

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@router.post("/create-order")
async def create_order(request: CheckoutSessionRequest):
    """
    Creates a real Razorpay order
    """
    try:
        plans = {
            "monthly": 49900,   # ₹499 in paise
            "yearly": 399900,   # ₹3999 in paise
            "lifetime": 999900  # ₹9999 in paise
        }

        if request.plan_id not in plans:
            raise HTTPException(status_code=400, detail="Invalid plan")

        order_data = {
            "amount": plans[request.plan_id],
            "currency": settings.CURRENCY,
            "receipt": f"receipt_{request.user_id}_{request.plan_id}",
            "notes": {
                "user_id": str(request.user_id),
                "email": request.email,
                "plan_id": request.plan_id
            }
        }

        order = razorpay_client.order.create(order_data)

        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.RAZORPAY_KEY_ID,
            "user_email": request.email,
            "plan_id": request.plan_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.post("/verify-payment")
async def verify_payment(
    request: Request,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Verifies Razorpay payment signature, updates subscription, and sends confirmation email.
    """
    try:
        body = await request.json()

        razorpay_order_id = body.get("razorpay_order_id")
        razorpay_payment_id = body.get("razorpay_payment_id")
        razorpay_signature = body.get("razorpay_signature")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            raise HTTPException(status_code=400, detail="Missing payment fields")

        # Use service layer — this also sends the confirmation email
        result = await payment_service.verify_payment(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature,
            db
        )

        return result

    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Payment signature verification failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Handle Razorpay webhooks for payment events
    """
    try:
        webhook_signature = request.headers.get("X-Razorpay-Signature")

        if not webhook_signature:
            raise HTTPException(status_code=400, detail="No webhook signature")

        body = await request.body()
        body_str = body.decode("utf-8")
        payload = json.loads(body_str)

        result = await payment_service.handle_webhook(payload, webhook_signature, db)

        return {"status": "success", "event": result.get("event")}

    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscription/{user_id}")
async def get_subscription(
    user_id: int,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Check subscription status for a user
    """
    try:
        subscription = await payment_service.get_subscription_status(user_id, db)
        return subscription
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel-subscription")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Cancel user's subscription.
    """
    try:
        await db.execute("""
            UPDATE subscriptions
            SET is_active = false,
                end_date = NOW(),
                updated_at = NOW()
            WHERE user_id = $1 AND is_active = true
        """, request.user_id)

        return {"success": True, "message": "Subscription cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mock-payment-success")
async def mock_payment_success(
    request: MockPaymentRequest,
    db: asyncpg.Connection = Depends(get_async_db)
):
    await payment_service.update_subscription(request.user_id, request.plan_id, db)
    return {"success": True}