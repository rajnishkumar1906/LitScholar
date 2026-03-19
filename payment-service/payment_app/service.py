import time
import random
import asyncpg
import razorpay
import httpx
from datetime import datetime, timedelta
from core.config import settings

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class PaymentService:
    async def send_payment_email(self, email: str, user_id: int, plan_id: str, amount: int, payment_id: str):
        """
        Trigger email via email service
        """
        try:
            # Map plan_id to readable name
            plan_names = {
                "monthly": "Monthly Subscription",
                "yearly": "Yearly Subscription",
                "lifetime": "Lifetime Access"
            }
            
            plan_name = plan_names.get(plan_id, plan_id)
            amount_inr = amount / 100  # Convert from paise to rupees
            
            # Create HTML email content
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 10px;">
                    <h2 style="color: #4F46E5;">🎉 Payment Successful!</h2>
                    
                    <p>Hello,</p>
                    
                    <p>Thank you for your payment! Your subscription has been activated successfully.</p>
                    
                    <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p><strong>Plan:</strong> {plan_name}</p>
                        <p><strong>Amount:</strong> ₹{amount_inr:.2f}</p>
                        <p><strong>Payment ID:</strong> {payment_id}</p>
                        <p><strong>Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                    </div>
                    
                    <p>You now have access to all premium features!</p>
                    
                    <hr style="border: none; border-top: 1px solid #eaeaea; margin: 30px 0;">
                    
                    <p style="text-align: center; color: #666;">
                        Happy Reading! 📚<br>
                        <strong>The LitScholar Team</strong>
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Call email service
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.EMAIL_SERVICE_URL}/send-email",
                    json={
                        "email": [email],
                        "subject": "🎉 Payment Successful - LitScholar Subscription",
                        "body": html_body
                    },
                    timeout=5.0
                )
            print(f"📧 Payment confirmation email sent to {email}")
            
        except Exception as e:
            print(f"⚠️ Failed to send payment email: {e}")

    async def create_checkout_session(self, user_id: int, email: str, plan_id: str):
        """
        Create a real Razorpay order
        """
        print(f"💰 Creating Razorpay order for {email} - Plan: {plan_id}")
        
        # Define plan prices (in paise - ₹1 = 100 paise)
        plans = {
            "monthly": 49900,    # ₹499
            "yearly": 399900,     # ₹3999
            "lifetime": 999900    # ₹9999
        }
        
        if plan_id not in plans:
            raise ValueError(f"Invalid plan: {plan_id}")
        
        # Create Razorpay order
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
        Verify payment signature and update subscription
        """
        try:
            # Verify signature
            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            }
            
            razorpay_client.utility.verify_payment_signature(params_dict)
            print(f"✅ Payment signature verified for order: {order_id}")
            
            # Fetch order details to get user info
            order = razorpay_client.order.fetch(order_id)
            user_id = int(order["notes"]["user_id"])
            email = order["notes"]["email"]
            plan_id = order["notes"]["plan_id"]
            amount = order["amount"]
            
            # Update subscription in database
            result = await self.update_subscription(user_id, plan_id, db, payment_id)
            
            # 🚀 SEND PAYMENT CONFIRMATION EMAIL
            await self.send_payment_email(email, user_id, plan_id, amount, payment_id)
            
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
        Update subscription after successful payment
        """
        from datetime import datetime, timedelta
        
        # Calculate expiration based on plan
        now = datetime.utcnow()
        
        if plan_id == "monthly":
            expires_at = now + timedelta(days=30)
        elif plan_id == "yearly":
            expires_at = now + timedelta(days=365)
        elif plan_id == "lifetime":
            expires_at = now + timedelta(days=36500)  # ~100 years
        else:
            expires_at = now + timedelta(days=30)
        
        # Insert or update subscription
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
        Get user's subscription status with auto-expiry check
        """
        row = await db.fetchrow(
            "SELECT plan_name, is_active, expires_at FROM subscriptions WHERE user_id = $1",
            user_id
        )
        
        if not row:
            return {
                "user_id": user_id, 
                "is_active": False,
                "plan_name": None,
                "expires_at": None
            }
        
        # Check if expired
        expires_at = row["expires_at"]
        is_active = row["is_active"]
        
        if expires_at and expires_at < datetime.utcnow():
            is_active = False
            # Update DB if expired
            await db.execute(
                "UPDATE subscriptions SET is_active = FALSE WHERE user_id = $1", 
                user_id
            )
        
        return {
            "user_id": user_id,
            "plan_name": row["plan_name"],
            "is_active": is_active,
            "expires_at": expires_at.timestamp() if expires_at else None
        }
    
    async def handle_webhook(self, payload: dict, signature: str, db: asyncpg.Connection):
        """
        Handle Razorpay webhook events
        """
        # Verify webhook signature
        is_valid = razorpay_client.utility.verify_webhook_signature(
            json.dumps(payload), 
            signature, 
            settings.RAZORPAY_WEBHOOK_SECRET
        )
        
        if not is_valid:
            raise Exception("Invalid webhook signature")
        
        event = payload.get("event")
        
        if event == "payment.captured":
            payment = payload["payload"]["payment"]["entity"]
            order_id = payment["order_id"]
            
            # Fetch order details
            order = razorpay_client.order.fetch(order_id)
            user_id = int(order["notes"]["user_id"])
            email = order["notes"]["email"]
            plan_id = order["notes"]["plan_id"]
            amount = order["amount"]
            
            # Update subscription
            await self.update_subscription(
                user_id, 
                plan_id, 
                db, 
                payment["id"]
            )
            
            # 🚀 SEND PAYMENT CONFIRMATION EMAIL VIA WEBHOOK
            await self.send_payment_email(email, user_id, plan_id, amount, payment["id"])
            
            print(f"✅ Webhook: Subscription activated for user {user_id}")
        
        return {"event": event, "status": "processed"}

payment_service = PaymentService()