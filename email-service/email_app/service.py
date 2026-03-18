import time
import asyncpg

class EmailService:
    async def send_mock_email(self, email: str, subject: str, body: str, db: asyncpg.Connection = None, template: str = None):
        print(f"📧 [MOCK EMAIL] Sending to: {email}")
        print(f"📧 [MOCK EMAIL] Subject: {subject}")
        print(f"📧 [MOCK EMAIL] Body: {body}")
        
        import anyio
        await anyio.sleep(1) # Asynchronous sleep
        
        print(f"✅ [MOCK EMAIL] Successfully sent to {email}")
        
        # Log to DB if connection provided
        if db:
            try:
                await db.execute("""
                    INSERT INTO email_logs (recipient_email, subject, template_name, status, sent_at)
                    VALUES ($1, $2, $3, 'sent', NOW())
                """, email, subject, template)
            except Exception as e:
                print(f"⚠️ Failed to log email: {e}")

    async def trigger_welcome_email(self, email: str, username: str = None, db: asyncpg.Connection = None):
        subject = "Welcome to LitScholar! 📚"
        user = username or email.split('@')[0]
        body = f"""
        Hi {user},
        
        Welcome to LitScholar! We're thrilled to have you here.
        Explore our collection and start your reading journey today!
        
        Happy Reading,
        The LitScholar Team
        """
        await self.send_mock_email(email, subject, body, db, template="welcome_email")

email_service = EmailService()
