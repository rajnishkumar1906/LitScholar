# identity-service/core/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings
import anyio
from datetime import datetime

class EmailService:
    async def send_email(self, to_email: str, subject: str, body: str, template: str = None):
        """
        Actually send real email via SMTP, with a fallback for development.
        """
        try:
            print(f"📧 Preparing to send email to: {to_email}")
            print(f"📧 Subject: {subject}")
            
            # 💡 DEVELOPMENT FALLBACK
            if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD or settings.SMTP_USERNAME == "":
                print("⚠️ [DEV MODE] SMTP credentials missing. Skipping real email send.")
                print(f"📝 MOCK EMAIL LOG: To: {to_email} | Subject: {subject}")
                return True

            # Create message
            msg = MIMEMultipart()
            msg["From"] = settings.SENDER_EMAIL or settings.SMTP_USERNAME
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            # Connect to SMTP server
            print(f"🔌 Connecting to {settings.SMTP_SERVER}:{settings.SMTP_PORT}...")
            
            # Handle different ports (587 for TLS, 465 for SSL, others for plain)
            if settings.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)
            else:
                server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
                if settings.SMTP_PORT == 587:
                    server.starttls()
            
            # Login
            print(f"🔐 Logging in as {settings.SMTP_USERNAME}...")
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            # Send email
            print("📤 Sending email...")
            server.send_message(msg)
            server.quit()
            
            print(f"✅ [REAL EMAIL] Successfully sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ [REAL EMAIL] Failed to send to {to_email}: {e}")
            print(f"Error details: {str(e)}")
            # Fallback to mock in dev
            print(f"📝 FALLBACK MOCK LOG: To: {to_email} | Subject: {subject}")
            return False

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

    async def trigger_password_reset_email(self, email: str, username: str, otp: str):
        subject = "Your LitScholar Password Reset OTP 🔐"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <h2 style="color: #4F46E5;">Password Reset Request</h2>
                <p>Hi {username},</p>
                <p>We received a request to reset your password for your LitScholar account.</p>
                <p>Use the following 6-digit OTP to reset your password. This code will expire in 10 minutes.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <span style="background-color: #F3F4F6; color: #1F2937; padding: 15px 30px; font-size: 32px; font-weight: bold; border-radius: 10px; letter-spacing: 5px;">
                        {otp}
                    </span>
                </div>
                <p>If you didn't request a password reset, you can safely ignore this email.</p>
                <p>For security, never share this code with anyone.</p>
                <br>
                <p>The LitScholar Team</p>
            </div>
        </body>
        </html>
        """
        await self.send_email(email, subject, body, template="password_reset")

    async def trigger_login_email(self, email: str):
        username = email.split('@')[0]
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        subject = "🔐 New Login to LitScholar"
        body = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="max-width: 550px; margin: 40px auto; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;">
                <div style="padding: 30px 40px;">
                    <h2 style="color: #4F46E5;">Security Alert: New Login</h2>
                    <p>Hi {username},</p>
                    <p>A new sign-in was detected for your LitScholar account.</p>
                    <div style="background-color: #f8fafc; padding: 20px; margin: 20px 0;">
                        <p><strong>Account:</strong> {email}</p>
                        <p><strong>Time:</strong> {current_time} UTC</p>
                    </div>
                    <p>If this wasn't you, please secure your account immediately.</p>
                </div>
            </div>
        </body>
        </html>
        """
        await self.send_email(email, subject, body, template="login_email")

    async def send_payment_confirmation(self, email: str, username: str, plan_name: str, amount: float, payment_id: str, expiry_date: str):
        subject = f'Payment confirmed! your LitScholar {plan_name} is active'
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
        await self.send_email(email, subject, body, template='payment_confirmation')

# Create instance
email_service = EmailService()
