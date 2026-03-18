from fastapi import APIRouter, BackgroundTasks, Depends
from email_app.schemas import EmailSchema, WelcomeEmailRequest
from email_app.service import email_service
from core.db import get_async_db
import asyncpg

router = APIRouter()

@router.post("/send-email")
async def send_email(
    email_data: EmailSchema, 
    background_tasks: BackgroundTasks,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Sends a general transactional email
    """
    for email in email_data.email:
        background_tasks.add_task(email_service.send_mock_email, email, email_data.subject, email_data.body, db)
    
    return {"message": "Emails are being sent in the background"}

@router.post("/welcome")
async def welcome_email(
    request: WelcomeEmailRequest, 
    background_tasks: BackgroundTasks,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    Sends a welcome email to a newly registered user
    """
    background_tasks.add_task(email_service.trigger_welcome_email, request.email, request.username, db)
    
    return {"message": "Welcome email is being sent"}
