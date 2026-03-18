import time
import random
import asyncpg

class PaymentService:
    async def create_checkout_session(self, user_id: int, email: str, plan_id: str):
        print(f"💰 [MOCK PAYMENT] Creating checkout session for {email}")
        print(f"💰 [MOCK PAYMENT] Plan ID: {plan_id}")
        
        # Generate a mock checkout URL
        checkout_url = f"https://mock-checkout.litscholar.com/pay/{random.getrandbits(32)}"
        return checkout_url

    async def update_subscription(self, user_id: int, plan_id: str, db: asyncpg.Connection):
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        await db.execute("""
            INSERT INTO subscriptions (user_id, plan_name, is_active, expires_at, updated_at)
            VALUES ($1, $2, TRUE, $3, NOW())
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                plan_name = EXCLUDED.plan_name,
                is_active = TRUE,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
        """, user_id, plan_id, expires_at)
        
        return {
            "user_id": user_id,
            "plan_name": plan_id,
            "is_active": True,
            "expires_at": expires_at.timestamp()
        }

    async def get_subscription_status(self, user_id: int, db: asyncpg.Connection):
        row = await db.fetchrow(
            "SELECT plan_name, is_active, expires_at FROM subscriptions WHERE user_id = $1",
            user_id
        )
        
        if not row:
            return {"user_id": user_id, "is_active": False}
        
        # Check if expired
        expires_at = row["expires_at"]
        is_active = row["is_active"]
        
        from datetime import datetime
        if expires_at < datetime.utcnow():
            is_active = False
            # Update DB if expired
            await db.execute("UPDATE subscriptions SET is_active = FALSE WHERE user_id = $1", user_id)
            
        return {
            "user_id": user_id,
            "plan_name": row["plan_name"],
            "is_active": is_active,
            "expires_at": expires_at.timestamp()
        }

payment_service = PaymentService()
