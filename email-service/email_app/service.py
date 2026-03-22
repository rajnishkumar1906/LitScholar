# email_app/service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings
import anyio

class EmailService:
    async def send_email(self, to_email: str, subject: str, body: str, template: str = None):
        """
        Actually send real email via Gmail SMTP
        """
        try:
            print(f"📧 Preparing to send email to: {to_email}")
            print(f"📧 Subject: {subject}")
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = settings.SENDER_EMAIL
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            # Connect to Gmail SMTP
            print(f"🔌 Connecting to {settings.SMTP_SERVER}:{settings.SMTP_PORT}...")
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            
            # Login
            print(f"🔐 Logging in as {settings.SMTP_USERNAME}...")
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            # Send email
            print("📤 Sending email...")
            server.send_message(msg)
            server.quit()
            
            print(f"✅ [REAL EMAIL] Successfully sent to {to_email}")
            
            # Log to console (you can add DB logging later)
            return True
            
        except Exception as e:
            print(f"❌ [REAL EMAIL] Failed to send to {to_email}: {e}")
            print(f"Error details: {str(e)}")
            return False

    async def send_mock_email(self, email: str, subject: str, body: str, template: str = None):
        """
        Keep mock for fallback, but try real email first
        """
        print(f"📧 [MOCK] Would send to: {email}")
        print(f"📧 [MOCK] Subject: {subject}")
        
        # Try to send real email
        await self.send_email(email, subject, body, template)
        
        await anyio.sleep(1)
        print(f"✅ [MOCK] Process completed for {email}")

    async def trigger_welcome_email(self, email: str, username: str = None):
        subject = "Welcome to LitScholar! 📚"
        user = username or email.split('@')[0]
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4F46E5;">Welcome to LitScholar!</h2>
                <p>Hi {user},</p>
                <p>Welcome to LitScholar! We're thrilled to have you here.</p>
                <p>Explore our collection and start your reading journey today!</p>
                <br>
                <p>Happy Reading! 📚</p>
                <p>The LitScholar Team</p>
            </div>
        </body>
        </html>
        """
        await self.send_email(email, subject, body, template="welcome_email")

    async def send_payment_confirmation(self,email:str,username:str,plan_name : str,amount:float,payment_id :str, expiry_date:str):
        subject = f'Payment confirmed! yout LitScholar {plan_name} is active'
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <h2 style="color: #4F46E5;">Thank you for your purchase, {username}!</h2>
                <p>Your payment has been successfully processed. You now have full access to <strong>LitScholar Premium</strong>.</p>
                
                <div style="background-color: #f9fafb; padding: 15px; border-radius: 8px;">
                    <p><strong>Plan:</strong> {plan_name}</p>
                    <p><strong>Amount Paid:</strong> ₹{amount}</p>
                    <p><strong>Payment ID:</strong> {payment_id}</p>
                    <p><strong>Valid Until:</strong> {expiry_date}</p>
                </div>

                <p style="margin-top: 20px;">Enjoy your reading journey!</p>
                <br>
                <p>Best regards,<br>The LitScholar Team</p>
            </div>
        </body>
        </html>
        """
        await self.send_email(email,subject,body,template='payment_confirmation')
        
# Create instance
email_service = EmailService()