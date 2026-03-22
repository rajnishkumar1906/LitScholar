import time
import json
import asyncpg
import razorpay
import httpx
from datetime import datetime, timedelta
from core.config import settings

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class PaymentService:
    async def send_payment_email(self, email: str, plan_id: str, amount: int, payment_id: str, expires_at: datetime):
        """
        Trigger structured email via the dedicated email service microservice
        """
        try:
            plan_names = {
                "monthly": "Monthly Subscription",
                "yearly": "Yearly Subscription",
                "lifetime": "Lifetime Access"
            }
            
            plan_name = plan_names.get(plan_id, plan_id)
            amount_inr = amount / 100 
            
            # Formatted date for the email service payload
            expiry_str = expires_at.strftime('%Y-%m-%d') if plan_id != "lifetime" else "Lifetime Access"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.EMAIL_SERVICE_URL}/payment-confirmation",
                    json={
                        "email": email,
                        "username": email.split('@')[0],
                        "plan_name": plan_name,
                        "amount": amount_inr,
                        "payment_id": payment_id,
                        "expiry_date": expiry_str
                    },
                    timeout=5.0
                )
                response.raise_for_status()
                
            print(f"✅ Payment confirmation email triggered for {email}")
            
        except Exception as e:
            print(f"⚠️ Email Service Error: {e}")

    async def create_checkout_session(self, user_id: int, email: str, plan_id: str):
        """
        Create a real Razorpay order for the frontend
        """
        plans = {
            "monthly": 49900,    # ₹499
            "yearly": 399900,    # ₹3999
            "lifetime": 999900   # ₹9999
        }
        
        if plan_id not in plans:
            raise ValueError(f"Invalid plan: {plan_id}")
        
        order_data = {
            "amount": plans[plan_id],
            "currency": settings.CURRENCY,
            "receipt": f"receipt_{user_id}_{plan_id}_{int(time.time())}",
            "notes": {
                "user_id": str(user_id),
                "email": email,
                "plan_id": plan_id
            }
        }
        
        order = razorpay_client.order.create(order_data)
        
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.RAZORPAY_KEY_ID,
            "user_email": email,
            "plan_id": plan_id,
            "user_id": user_id
        }

    async def verify_payment(self, order_id: str, payment_id: str, signature: str, db: asyncpg.Connection):
        """
        Verify payment signature and update subscription manually from frontend
        """
        try:
            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            }
            
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Fetch order details to get user metadata
            order = razorpay_client.order.fetch(order_id)
            user_id = int(order["notes"]["user_id"])
            email = order["notes"]["email"]
            plan_id = order["notes"]["plan_id"]
            amount = order["amount"]
            
            # Update DB
            result = await self.update_subscription(user_id, plan_id, db, payment_id)
            
            # Trigger Email
            expires_at = datetime.fromtimestamp(result["expires_at"])
            await self.send_payment_email(email, plan_id, amount, payment_id, expires_at)
            
            return {
                "success": True,
                "message": "Payment verified and subscription activated",
                "payment_id": payment_id,
                "subscription": result
            }
            
        except razorpay.errors.SignatureVerificationError:
            print(f"❌ Signature verification failed for order: {order_id}")
            raise Exception("Payment signature verification failed")

    async def update_subscription(self, user_id: int, plan_id: str, db: asyncpg.Connection, payment_id: str = None):
        """
        Idempotent update of subscription in the database
        """
        now = datetime.utcnow()
        
        if plan_id == "monthly":
            expires_at = now + timedelta(days=30)
        elif plan_id == "yearly":
            expires_at = now + timedelta(days=365)
        elif plan_id == "lifetime":
            expires_at = now + timedelta(days=36500) # ~100 years
        else:
            expires_at = now + timedelta(days=30)
        
        result = await db.fetchrow("""
            INSERT INTO subscriptions (user_id, plan_name, is_active, expires_at, updated_at, payment_id)
            VALUES ($1, $2, TRUE, $3, NOW(), $4)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                plan_name = EXCLUDED.plan_name,
                is_active = TRUE,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW(),
                payment_id = EXCLUDED.payment_id
            RETURNING user_id, plan_name, is_active, expires_at
        """, user_id, plan_id, expires_at, payment_id)
        
        print(f"✅ Subscription updated for user {user_id} - Plan: {plan_id}")
        
        return {
            "user_id": result["user_id"],
            "plan_name": result["plan_name"],
            "is_active": result["is_active"],
            "expires_at": result["expires_at"].timestamp()
        }

    async def get_subscription_status(self, user_id: int, db: asyncpg.Connection):
        """
        Check user status and auto-expire if past the date
        """
        row = await db.fetchrow(
            "SELECT plan_name, is_active, expires_at FROM subscriptions WHERE user_id = $1",
            user_id
        )
        
        if not row:
            return {"user_id": user_id, "is_active": False, "plan_name": None, "expires_at": None}
        
        is_active = row["is_active"]
        expires_at = row["expires_at"]
        
        if expires_at and expires_at < datetime.utcnow():
            is_active = False
            await db.execute("UPDATE subscriptions SET is_active = FALSE WHERE user_id = $1", user_id)
        
        return {
            "user_id": user_id,
            "plan_name": row["plan_name"],
            "is_active": is_active,
            "expires_at": expires_at.timestamp() if expires_at else None
        }
    
    async def handle_webhook(self, payload: dict, signature: str, db: asyncpg.Connection):
        """
        Handle Razorpay webhook events for asynchronous payment success
        """
        # Verify signature using compact JSON string
        raw_payload = json.dumps(payload, separators=(',', ':'))
        is_valid = razorpay_client.utility.verify_webhook_signature(
            raw_payload, 
            signature, 
            settings.RAZORPAY_WEBHOOK_SECRET
        )
        
        if not is_valid:
            raise Exception("Invalid webhook signature")
        
        event = payload.get("event")
        
        if event == "payment.captured":
            payment = payload["payload"]["payment"]["entity"]
            order_id = payment["order_id"]
            
            # Fetch metadata from order notes
            order = razorpay_client.order.fetch(order_id)
            user_id = int(order["notes"]["user_id"])
            email = order["notes"]["email"]
            plan_id = order["notes"]["plan_id"]
            amount = order["amount"]
            
            # Update Sub and Trigger Email
            result = await self.update_subscription(user_id, plan_id, db, payment["id"])
            expires_at = datetime.fromtimestamp(result["expires_at"])
            await self.send_payment_email(email, plan_id, amount, payment["id"], expires_at)
            
            print(f"✅ Webhook processed: Subscription active for user {user_id}")
        
        return {"event": event, "status": "processed"}

payment_service = PaymentService()