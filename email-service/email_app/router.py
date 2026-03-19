# email_app/router.py - Add payment email endpoint
from fastapi import APIRouter, BackgroundTasks
from email_app.schemas import EmailSchema, WelcomeEmailRequest, PaymentEmailRequest
from email_app.service import email_service

router = APIRouter()

# Existing endpoints
@router.post("/send-email")
async def send_email(
    email_data: EmailSchema, 
    background_tasks: BackgroundTasks,
):
    """
    Sends a general transactional email
    """
    for email in email_data.email:
        background_tasks.add_task(
            email_service.send_email, 
            email, 
            email_data.subject, 
            email_data.body
        )
    
    return {"message": "Emails are being sent"}

@router.post("/welcome")
async def welcome_email(
    request: WelcomeEmailRequest, 
    background_tasks: BackgroundTasks,
):
    """
    Sends a welcome email to a newly registered user
    """
    background_tasks.add_task(
        email_service.trigger_welcome_email, 
        request.email, 
        request.username
    )
    
    return {"message": "Welcome email is being sent"}

# 🚀 NEW: Payment confirmation email endpoint
@router.post("/payment-confirmation")
async def payment_confirmation_email(
    request: PaymentEmailRequest, 
    background_tasks: BackgroundTasks,
):
    """
    Sends a payment confirmation email after successful subscription
    """
    background_tasks.add_task(
        email_service.send_payment_confirmation,
        email=request.email,
        username=request.username,
        plan_name=request.plan_name,
        amount=request.amount,
        payment_id=request.payment_id,
        expiry_date=request.expiry_date
    )
    
    return {"message": "Payment confirmation email is being sent"}